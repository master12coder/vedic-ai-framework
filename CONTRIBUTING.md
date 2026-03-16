# Contributing to Vedic AI Framework

Thank you for your interest in contributing! This project bridges ancient Vedic
wisdom with modern AI — contributions from both Jyotish scholars and software
engineers are welcome.

## Getting Started

```bash
git clone https://github.com/<org>/vedic-ai-framework.git
cd vedic-ai-framework
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ollama]"
pytest                # all 224+ tests must pass
```

See [docs/development/SETUP.md](docs/development/SETUP.md) for detailed setup.

## Development Workflow

1. **Create a branch** from `main`: `git checkout -b feat/your-feature`
2. **Make changes** following the [Style Guide](docs/development/STYLE_GUIDE.md)
3. **Run checks**: `make lint typecheck test`
4. **Commit** using [Conventional Commits](#commit-messages)
5. **Open a PR** using the [PR template](.github/PULL_REQUEST_TEMPLATE.md)

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

| Type       | When to use                          |
|------------|--------------------------------------|
| `feat`     | New feature                          |
| `fix`      | Bug fix                              |
| `docs`     | Documentation only                   |
| `refactor` | Code change that neither fixes nor adds |
| `test`     | Adding or updating tests             |
| `chore`    | Build process, CI, tooling           |
| `safety`   | Gemstone/interpretation safety fix   |
| `perf`     | Performance improvement              |

**Scopes:** `compute`, `interpret`, `knowledge`, `learn`, `deliver`, `cli`,
`scripts`, `docs`, `config`

## Architecture Rules

These are **non-negotiable**:

1. **Computation is LOCKED** — Swiss Ephemeris positions are never approximated
2. **No LLM in compute/** — deterministic calculations only
3. **Dependencies flow inward** — `deliver → interpret → compute`, never reverse
4. **Dataclasses only** — no raw `dict` for domain data
5. **YAML is truth** — astrological rules live in `knowledge/*.yaml`
6. **Gemstone safety** — never recommend maraka planet stones (see
   [GEMSTONE_SAFETY.md](docs/vedic/GEMSTONE_SAFETY.md))

## What to Contribute

### High-Impact Areas

- **Knowledge YAML files** — more scripture rules, additional yoga definitions
- **Scripture database** — BPHS chapter coverage, Brihat Jataka, Phaladeepika
- **Test cases** — especially safety tests for gemstone recommendations
- **LLM backends** — new providers via the `LLMBackend` protocol
- **Prompt templates** — improved interpretation accuracy

### Vedic Knowledge Contributions

If you are a Jyotish scholar or practitioner:

- Add scripture rules to `jyotish/scriptures/bphs/`
- Review and correct `jyotish/knowledge/lordship_rules.yaml`
- Submit Pandit Ji corrections via `jyotish correct` CLI
- Add life event validation data for accuracy testing

## Testing

```bash
make test           # full suite
make test-safety    # gemstone safety tests only
pytest -k "mithuna" # run specific tests
```

All PRs must pass CI. Safety-critical changes require explicit test coverage.
See [docs/development/TESTING.md](docs/development/TESTING.md).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be
respectful of diverse astrological traditions and cultural perspectives.

## Questions?

Open a [Discussion](https://github.com/<org>/vedic-ai-framework/discussions)
or reach out to the maintainers.
