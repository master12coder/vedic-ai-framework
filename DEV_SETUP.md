# SkillCat Dev Setup — New Machine

## First time on a new PC (30 seconds)

```bash
git clone <repo-url>
cd skillcat
bash setup.sh
```

That's it. Everything is configured automatically:
- ✅ nlm CLI installed globally
- ✅ Git hooks active (auto re-index on commit/push)
- ✅ Initial doc index built

---

## What setup.sh does

| Step | What happens |
|------|-------------|
| Install deps | `pip install rank-bm25 pypdf python-docx` |
| Install nlm | Copies `tools/nlm/nlm.py` → `/usr/local/bin/nlm` |
| Git hooks | `git config core.hooksPath .githooks` — points git to committed hooks |
| Initial index | Indexes `docs/`, `specs/`, `.claude/`, root MD files |

---

## How NLM stays in sync automatically

```
git commit  →  post-commit hook  →  re-indexes changed files only
git push    →  pre-push hook     →  full re-index of docs/ specs/
```

You never run nlm manually. It stays current with your repo.

---

## After cloning on a new PC — index your large spec files

These are not committed to git (too large), so add them manually once:

```bash
nlm add /path/to/lms_functional_spec.pdf
nlm add /path/to/nrc_architecture.md
nlm add /path/to/b2b_dashboard_spec.md
```

The index saves to `~/.nlm_index/` on your machine.

---

## Daily commands

```bash
nlm query "billing stripe"          # search docs
nlm query "auth flow" --top-k 3    # fewer results
nlm list                            # see all indexed docs
nlm stats                           # index summary
```

---

## Repo structure

```
.githooks/
  post-commit     # auto re-index on commit (committed to repo)
  pre-push        # full sync on push (committed to repo)
tools/
  nlm/
    nlm.py        # the CLI tool (committed to repo)
setup.sh          # run once on new machine
```
