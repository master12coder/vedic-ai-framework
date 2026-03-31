#!/usr/bin/env python3
"""
NLM - Natural Language Memory (v1.0.0)
Local BM25 RAG CLI for auto-injecting relevant documentation context.
Zero external APIs. Everything local. BM25 keyword search only.

Indexes DOCUMENTATION only (not source code). Each project gets its own index.
"""

import argparse
import json
import os
import pickle
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"

# Per-project index directory
BASE_INDEX_DIR = os.path.expanduser("~/.nlm_index")

# Documentation file types only — NOT source code
DOC_EXTENSIONS = {
    ".md", ".txt", ".rst", ".html", ".css",
    ".yaml", ".yml", ".json", ".xml", ".sql", ".sh",
    ".env.example",
}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}
ALL_EXTENSIONS = DOC_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS

CHUNK_SIZE = 600  # words
CHUNK_OVERLAP = 80  # words
MIN_CHUNK_WORDS = 20


def get_project_name():
    """Derive project name from git remote or directory name."""
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        # Extract repo name from URL
        name = url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name or "default"
    except Exception:
        return Path.cwd().name or "default"


def get_index_dir():
    """Get per-project index directory."""
    project = get_project_name()
    return os.path.join(BASE_INDEX_DIR, project)


def get_index_file():
    """Get per-project index file path."""
    return os.path.join(get_index_dir(), "index.pkl")


def tokenize(text):
    """Simple word tokenization for BM25."""
    return re.findall(r'\w+', text.lower())


def chunk_text(text, source_file):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        if len(chunk_words) >= MIN_CHUNK_WORDS:
            chunks.append({
                "text": " ".join(chunk_words),
                "source": source_file,
                "chunk_idx": len(chunks),
                "start_word": start,
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def read_text_file(filepath):
    """Read a text/markup file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def read_pdf_file(filepath):
    """Read a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts)
    except ImportError:
        print("Warning: pypdf not installed. Skipping PDF.", file=sys.stderr)
        return None
    except Exception:
        return None


def read_docx_file(filepath):
    """Read a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        print("Warning: python-docx not installed. Skipping DOCX.", file=sys.stderr)
        return None
    except Exception:
        return None


def read_file(filepath):
    """Read file based on extension."""
    ext = Path(filepath).suffix.lower()
    if ext in PDF_EXTENSIONS:
        return read_pdf_file(filepath)
    elif ext in DOCX_EXTENSIONS:
        return read_docx_file(filepath)
    elif ext in DOC_EXTENSIONS:
        return read_text_file(filepath)
    return None


def load_index():
    """Load the BM25 index from disk."""
    index_file = get_index_file()
    if not os.path.exists(index_file):
        return {"documents": [], "chunks": [], "bm25": None}
    try:
        with open(index_file, "rb") as f:
            data = pickle.load(f)
        if not isinstance(data, dict) or "chunks" not in data:
            raise ValueError("Invalid index format")
        return data
    except (pickle.UnpicklingError, EOFError, ValueError, Exception) as e:
        backup = index_file + ".bak"
        try:
            if os.path.exists(index_file):
                os.rename(index_file, backup)
                print(f"Corrupted index backed up to {backup}", file=sys.stderr)
        except Exception:
            pass
        return {"documents": [], "chunks": [], "bm25": None}


def save_index(data):
    """Save index atomically via temp file + rename."""
    index_dir = get_index_dir()
    os.makedirs(index_dir, exist_ok=True)
    index_file = get_index_file()
    fd, tmp_path = tempfile.mkstemp(dir=index_dir, suffix=".pkl.tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            pickle.dump(data, f)
        os.replace(tmp_path, index_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


def rebuild_bm25(index_data):
    """Rebuild BM25 index from chunks."""
    if not index_data["chunks"]:
        index_data["bm25"] = None
        return
    try:
        from rank_bm25 import BM25Okapi
        corpus = [tokenize(c["text"]) for c in index_data["chunks"]]
        index_data["bm25"] = BM25Okapi(corpus)
    except ImportError:
        print("Error: rank-bm25 not installed. Run: pip3 install rank-bm25", file=sys.stderr)
        sys.exit(1)


def is_doc_file(filepath):
    """Check if a file is a documentation file (not source code)."""
    ext = Path(filepath).suffix.lower()
    return ext in ALL_EXTENSIONS


def cmd_add(args):
    """Add documentation files to the index."""
    index_data = load_index()
    existing_docs = {d["path"]: d for d in index_data["documents"]}
    files_to_process = []

    for filepath in args.files:
        path = os.path.abspath(filepath)
        if os.path.isdir(path):
            for root, dirs, filenames in os.walk(path):
                # Skip hidden dirs, node_modules, build dirs
                dirs[:] = [d for d in dirs if not d.startswith('.')
                           and d not in ('node_modules', '__pycache__', 'venv', '.venv',
                                         'build', 'dist', '.dart_tool', '.gradle')]
                for fn in filenames:
                    fp = os.path.join(root, fn)
                    if is_doc_file(fp):
                        files_to_process.append(fp)
        elif os.path.isfile(path):
            if is_doc_file(path):
                files_to_process.append(path)
            elif not args.quiet:
                print(f"Skipping non-doc file: {filepath}", file=sys.stderr)
        else:
            if not args.quiet:
                print(f"Skipping: {filepath} (not found)", file=sys.stderr)

    added = 0
    skipped = 0
    for fp in files_to_process:
        abs_path = os.path.abspath(fp)
        mtime = os.path.getmtime(abs_path)

        if abs_path in existing_docs and not args.force:
            if existing_docs[abs_path].get("mtime", 0) >= mtime:
                skipped += 1
                continue

        text = read_file(abs_path)
        if text is None or len(text.strip()) < 10:
            skipped += 1
            continue

        # Remove old chunks for this file
        index_data["chunks"] = [c for c in index_data["chunks"] if c["source"] != abs_path]
        index_data["documents"] = [d for d in index_data["documents"] if d["path"] != abs_path]

        chunks = chunk_text(text, abs_path)
        index_data["chunks"].extend(chunks)
        index_data["documents"].append({
            "path": abs_path,
            "mtime": mtime,
            "chunks": len(chunks),
            "indexed_at": datetime.now().isoformat(),
        })
        added += 1

    if added > 0:
        rebuild_bm25(index_data)
        save_index(index_data)

    if not args.quiet:
        print(f"Added: {added}, Skipped: {skipped}, Total docs: {len(index_data['documents'])}, Total chunks: {len(index_data['chunks'])}")


def cmd_query(args):
    """Query the index."""
    index_data = load_index()
    if not index_data["chunks"] or index_data["bm25"] is None:
        if args.json:
            print(json.dumps({"results": [], "query": args.query}))
        elif not args.quiet:
            print("Index is empty. Run: nlm add <docs-dir>")
        return

    query_tokens = tokenize(args.query)
    if not query_tokens:
        if not args.quiet:
            print("No valid query tokens.")
        return

    chunks = index_data["chunks"]
    bm25 = index_data["bm25"]

    # Filter by document if --doc specified
    if args.doc:
        doc_filter = args.doc.lower()
        filtered = [(i, c) for i, c in enumerate(chunks) if doc_filter in c["source"].lower()]
        if not filtered:
            if not args.quiet:
                print(f"No documents matching filter: {args.doc}")
            return
        from rank_bm25 import BM25Okapi
        corpus = [tokenize(c["text"]) for _, c in filtered]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:args.top_k]
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            chunk = filtered[idx][1]
            results.append({
                "score": round(float(scores[idx]), 4),
                "source": chunk["source"],
                "chunk_idx": chunk["chunk_idx"],
                "text": chunk["text"][:500],
            })
    else:
        scores = bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:args.top_k]
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            chunk = chunks[idx]
            results.append({
                "score": round(float(scores[idx]), 4),
                "source": chunk["source"],
                "chunk_idx": chunk["chunk_idx"],
                "text": chunk["text"][:500],
            })

    if args.json:
        print(json.dumps({"results": results, "query": args.query}, indent=2))
    elif args.quiet:
        for r in results:
            rel_path = os.path.relpath(r["source"])
            print(f"[{rel_path}:{r['chunk_idx']}] (score: {r['score']})")
            print(r["text"][:300])
            print("---")
    else:
        if not results:
            print("No relevant results found.")
            return
        for i, r in enumerate(results, 1):
            rel_path = os.path.relpath(r["source"])
            print(f"\n{'='*60}")
            print(f"Result {i} | Score: {r['score']} | {rel_path} (chunk {r['chunk_idx']})")
            print(f"{'='*60}")
            print(r["text"][:500])


def cmd_list(args):
    """List indexed documents."""
    index_data = load_index()
    if not index_data["documents"]:
        print("No documents indexed.")
        return
    print(f"{'Path':<60} {'Chunks':>6} {'Indexed At':>20}")
    print("-" * 90)
    for doc in sorted(index_data["documents"], key=lambda d: d["path"]):
        rel = os.path.relpath(doc["path"])
        ts = doc.get("indexed_at", "unknown")[:19]
        print(f"{rel:<60} {doc['chunks']:>6} {ts:>20}")


def cmd_delete(args):
    """Delete a document from the index."""
    index_data = load_index()
    path = os.path.abspath(args.file)
    before = len(index_data["documents"])
    index_data["documents"] = [d for d in index_data["documents"] if d["path"] != path]
    index_data["chunks"] = [c for c in index_data["chunks"] if c["source"] != path]
    after = len(index_data["documents"])

    if before != after:
        rebuild_bm25(index_data)
        save_index(index_data)
        if not getattr(args, 'quiet', False):
            print(f"Deleted: {os.path.relpath(path)}")
    else:
        if not getattr(args, 'quiet', False):
            print(f"Not found in index: {os.path.relpath(path)}")


def cmd_clear(args):
    """Clear the entire index."""
    save_index({"documents": [], "chunks": [], "bm25": None})
    print("Index cleared.")


def cmd_stats(args):
    """Show index statistics."""
    index_data = load_index()
    docs = index_data["documents"]
    chunks = index_data["chunks"]
    index_file = get_index_file()

    print(f"Project:        {get_project_name()}")
    print(f"Index location: {index_file}")
    print(f"Documents:      {len(docs)}")
    print(f"Total chunks:   {len(chunks)}")

    if os.path.exists(index_file):
        size = os.path.getsize(index_file)
        if size > 1024 * 1024:
            print(f"Index size:     {size / 1024 / 1024:.1f} MB")
        else:
            print(f"Index size:     {size / 1024:.1f} KB")

    if docs:
        ext_counts = {}
        for d in docs:
            ext = Path(d["path"]).suffix.lower() or "(none)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        print("\nBy file type:")
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1]):
            print(f"  {ext:<10} {count:>4} files")


def main():
    parser = argparse.ArgumentParser(
        prog="nlm",
        description="NLM - Local BM25 RAG CLI for documentation context"
    )
    parser.add_argument("--version", action="version", version=f"nlm {VERSION}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_add = subparsers.add_parser("add", help="Add doc files/directories to the index")
    p_add.add_argument("files", nargs="+", help="Files or directories to index")
    p_add.add_argument("--force", action="store_true", help="Re-index even if unchanged")
    p_add.add_argument("--quiet", action="store_true", help="Suppress output")

    p_query = subparsers.add_parser("query", help="Search the index")
    p_query.add_argument("query", help="Search query")
    p_query.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    p_query.add_argument("--doc", help="Filter by document path substring")
    p_query.add_argument("--json", action="store_true", help="JSON output")
    p_query.add_argument("--quiet", action="store_true", help="Compact output for hooks")

    subparsers.add_parser("list", help="List indexed documents")

    p_del = subparsers.add_parser("delete", help="Remove a document from the index")
    p_del.add_argument("file", help="File path to remove")
    p_del.add_argument("--quiet", action="store_true", help="Suppress output")

    subparsers.add_parser("clear", help="Clear the entire index")
    subparsers.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

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
