#!/usr/bin/env python3
"""
nlm - NotebookLM-style CLI for Claude Code
Local RAG: index docs, query relevant chunks, save tokens.

Usage:
  nlm add <file_or_dir>          # Index a document or folder
  nlm query "<question>" [opts]  # Search and return relevant chunks
  nlm list                       # List all indexed documents
  nlm delete <doc_id>            # Remove a document
  nlm clear                      # Wipe entire index
  nlm stats                      # Show index stats
  nlm export <query> [--json]    # Export chunks as JSON for piping

Designed for Claude Code: pipe output directly into context.
"""

import argparse
import json
import os
import pickle
import re
import sys
import textwrap
from pathlib import Path
from datetime import datetime

# ── Constants ──────────────────────────────────────────────────────────────
INDEX_DIR = Path.home() / ".nlm_index"
INDEX_FILE = INDEX_DIR / "index.pkl"
CHUNK_SIZE = 600       # words per chunk (tune: bigger = fewer tokens lost to overlap)
CHUNK_OVERLAP = 80     # words overlap between chunks
DEFAULT_TOP_K = 5      # chunks returned by default

# ── Storage ────────────────────────────────────────────────────────────────
def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "rb") as f:
            return pickle.load(f)
    return {"docs": {}, "chunks": [], "meta": {"created": str(datetime.now())}}

def save_index(idx):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(idx, f)

# ── Text Extraction ────────────────────────────────────────────────────────
def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            return f"[PDF read error: {e}]"
    
    elif suffix in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            return f"[DOCX read error: {e}]"
    
    elif suffix in (".md", ".txt", ".rst", ".log", ".json", ".yaml", ".yml",
                    ".py", ".js", ".ts", ".dart", ".go", ".java", ".swift",
                    ".html", ".css", ".sql", ".sh", ".env"):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[Read error: {e}]"
    
    else:
        # Try reading as plain text anyway
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return f"[Unsupported format: {suffix}]"

# ── Chunking ───────────────────────────────────────────────────────────────
def chunk_text(text: str, doc_id: str, source: str) -> list[dict]:
    words = text.split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    
    for i, start in enumerate(range(0, len(words), step)):
        chunk_words = words[start:start + CHUNK_SIZE]
        if len(chunk_words) < 20:  # skip tiny trailing chunks
            continue
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "id": f"{doc_id}::{i}",
            "doc_id": doc_id,
            "source": source,
            "chunk_idx": i,
            "text": chunk_text,
            "word_count": len(chunk_words),
        })
    
    return chunks

# ── BM25 Search ────────────────────────────────────────────────────────────
def build_bm25(chunks: list[dict]):
    from rank_bm25 import BM25Okapi
    tokenized = [c["text"].lower().split() for c in chunks]
    return BM25Okapi(tokenized)

def search(query: str, idx: dict, top_k: int = DEFAULT_TOP_K,
           filter_doc: str = None) -> list[dict]:
    chunks = idx["chunks"]
    if filter_doc:
        chunks = [c for c in chunks if filter_doc.lower() in c["source"].lower()
                  or filter_doc == c["doc_id"]]
    if not chunks:
        return []
    
    bm25 = build_bm25(chunks)
    scores = bm25.get_scores(query.lower().split())
    
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    results = []
    
    for score, chunk in ranked[:top_k]:
        results.append({**chunk, "score": round(float(score), 3)})
    
    return results

# ── Commands ───────────────────────────────────────────────────────────────
def cmd_add(args):
    idx = load_index()
    paths = []
    
    for target in args.paths:
        p = Path(target)
        if p.is_dir():
            # Recursively find all text files
            exts = {".pdf", ".docx", ".md", ".txt", ".rst", ".py", ".dart",
                    ".js", ".ts", ".json", ".yaml", ".yml", ".sql", ".html"}
            for f in p.rglob("*"):
                if f.suffix.lower() in exts and f.is_file():
                    paths.append(f)
        elif p.is_file():
            paths.append(p)
        else:
            print(f"⚠ Not found: {target}", file=sys.stderr)
    
    added = 0
    for path in paths:
        path = path.resolve()
        doc_id = str(path)
        
        if doc_id in idx["docs"] and not args.force:
            print(f"↩ Already indexed (use --force to re-index): {path.name}")
            continue
        
        print(f"📄 Indexing: {path.name} ...", end=" ", flush=True) if not args.quiet else None
        text = extract_text(path)
        
        if not text.strip() or "[read error" in text.lower():
            if not args.quiet: print(f"FAILED — {text[:80]}")
            continue
        
        # Remove old chunks for this doc
        idx["chunks"] = [c for c in idx["chunks"] if c["doc_id"] != doc_id]
        
        chunks = chunk_text(text, doc_id, str(path))
        idx["chunks"].extend(chunks)
        idx["docs"][doc_id] = {
            "path": str(path),
            "name": path.name,
            "size": path.stat().st_size,
            "chunks": len(chunks),
            "words": len(text.split()),
            "indexed_at": str(datetime.now()),
        }
        if not args.quiet: print(f"✓ {len(chunks)} chunks, {len(text.split()):,} words")
        added += 1
    
    save_index(idx)
    if not args.quiet:
        print(f"\n✅ Done. Added {added} doc(s). Total index: {len(idx['docs'])} docs, "
              f"{len(idx['chunks'])} chunks.")

def cmd_query(args):
    idx = load_index()
    if not idx["chunks"]:
        print("Index is empty. Run: nlm add <file>", file=sys.stderr)
        sys.exit(1)
    
    results = search(args.query, idx, top_k=args.top_k, filter_doc=args.doc)
    
    if not results:
        print("No relevant chunks found.", file=sys.stderr)
        sys.exit(0)
    
    if args.json:
        print(json.dumps(results, indent=2))
        return
    
    # Claude Code-friendly plain text output
    total_words = sum(r["word_count"] for r in results)
    sep = "─" * 70
    
    if not args.quiet:
        print(f"\n🔍 Query: {args.query}")
        print(f"📦 {len(results)} chunks returned | ~{total_words:,} words "
              f"(≈{total_words * 1.3:.0f} tokens)\n")
    
    for i, r in enumerate(results, 1):
        src_name = Path(r["source"]).name
        if not args.quiet:
            print(f"{sep}")
            print(f"[{i}] {src_name}  |  chunk #{r['chunk_idx']}  |  score {r['score']}")
            print(sep)
        print(r["text"])
        if not args.quiet:
            print()

def cmd_list(args):
    idx = load_index()
    docs = idx["docs"]
    if not docs:
        print("No documents indexed. Run: nlm add <file>")
        return
    
    print(f"\n{'ID':>4}  {'File':<40} {'Chunks':>6} {'Words':>8}  Indexed")
    print("─" * 75)
    for i, (doc_id, info) in enumerate(docs.items(), 1):
        name = info["name"][:38]
        print(f"{i:>4}  {name:<40} {info['chunks']:>6} {info['words']:>8}  "
              f"{info['indexed_at'][:16]}")
    print(f"\nTotal: {len(docs)} docs, {len(idx['chunks'])} chunks")

def cmd_delete(args):
    idx = load_index()
    target = args.doc_id
    
    # Match by name or path fragment
    matched = [k for k in idx["docs"] if target in k or target in idx["docs"][k]["name"]]
    
    if not matched:
        print(f"No document matching: {target}")
        return
    
    for doc_id in matched:
        name = idx["docs"][doc_id]["name"]
        del idx["docs"][doc_id]
        before = len(idx["chunks"])
        idx["chunks"] = [c for c in idx["chunks"] if c["doc_id"] != doc_id]
        removed = before - len(idx["chunks"])
        print(f"🗑 Removed: {name} ({removed} chunks)")
    
    save_index(idx)

def cmd_clear(args):
    if not args.yes:
        confirm = input("⚠ This will wipe the entire index. Type 'yes' to confirm: ")
        if confirm.strip().lower() != "yes":
            print("Cancelled.")
            return
    
    save_index({"docs": {}, "chunks": [], "meta": {"created": str(datetime.now())}})
    print("✅ Index cleared.")

def cmd_stats(args):
    idx = load_index()
    total_words = sum(c["word_count"] for c in idx["chunks"])
    print(f"\n📊 NotebookLM CLI Index Stats")
    print(f"   Documents : {len(idx['docs'])}")
    print(f"   Chunks    : {len(idx['chunks'])}")
    print(f"   Total words: {total_words:,} (~{int(total_words * 1.3):,} tokens)")
    print(f"   Index file : {INDEX_FILE}")
    print(f"   Index size : {INDEX_FILE.stat().st_size / 1024:.1f} KB" if INDEX_FILE.exists() else "")

def cmd_export(args):
    """Export query results as JSON — perfect for piping into Claude Code."""
    args.json = True
    args.quiet = True
    args.top_k = args.top_k
    cmd_query(args)

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="nlm",
        description="NotebookLM-style local RAG CLI — index docs, query chunks, save tokens.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          nlm add ./docs/                     # Index entire folder
          nlm add spec.pdf report.md          # Index specific files
          nlm query "how does billing work"   # Search (plain text, for Claude Code)
          nlm query "auth flow" --top-k 3     # Get 3 most relevant chunks
          nlm query "HVAC modules" --json     # JSON output
          nlm query "stripe" --doc billing    # Search within a specific doc
          nlm list                            # Show all indexed docs
          nlm stats                           # Index summary
          nlm delete spec.pdf                 # Remove a doc
          nlm clear                           # Wipe index
        
        Claude Code integration:
          # In CLAUDE.md or instructions.md, add:
          # Use `nlm query "<question>"` to search project docs before answering.
          # This saves tokens vs pasting full docs.
        """)
    )
    
    sub = parser.add_subparsers(dest="command", required=True)
    
    # add
    p_add = sub.add_parser("add", help="Index document(s) or folder")
    p_add.add_argument("paths", nargs="+", help="Files or directories to index")
    p_add.add_argument("--force", action="store_true", help="Re-index even if already indexed")
    p_add.add_argument("--quiet", action="store_true", help="Suppress output (for git hooks)")
    
    # query
    p_q = sub.add_parser("query", help="Search indexed docs and return relevant chunks")
    p_q.add_argument("query", help="Your search query / question")
    p_q.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help=f"Chunks to return (default {DEFAULT_TOP_K})")
    p_q.add_argument("--doc", help="Filter to a specific document (partial name match)")
    p_q.add_argument("--json", action="store_true", help="Output as JSON")
    p_q.add_argument("--quiet", action="store_true", help="Plain text only, no headers (for piping)")
    
    # list
    sub.add_parser("list", help="List all indexed documents")
    
    # delete
    p_del = sub.add_parser("delete", help="Remove a document from the index")
    p_del.add_argument("doc_id", help="Document name or path fragment")
    
    # clear
    p_clear = sub.add_parser("clear", help="Wipe the entire index")
    p_clear.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    
    # stats
    sub.add_parser("stats", help="Show index statistics")
    
    args = parser.parse_args()
    
    commands = {
        "add": cmd_add,
        "query": cmd_query,
        "list": cmd_list,
        "delete": cmd_delete,
        "clear": cmd_clear,
        "stats": cmd_stats,
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main()
