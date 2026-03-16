# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email the maintainer directly with details.
3. Include: description, reproduction steps, potential impact.
4. You will receive acknowledgment within 48 hours.

## Security Considerations

### API Keys

This project integrates with external LLM APIs. API keys are managed via
environment variables and are **never** committed to the repository.

- `GROQ_API_KEY` — Groq cloud inference
- `ANTHROPIC_API_KEY` — Claude API
- `OPENAI_API_KEY` — OpenAI API

**Never** hardcode API keys in source code, config files, or tests.

### Gemstone Safety

This is a **safety-critical** concern unique to this project. Incorrect
gemstone recommendations can cause real-world harm to users who follow
astrological advice.

**Safeguards in place:**
- Lordship rules injected into every LLM prompt per lagna
- Prohibited stone lists enforced at the prompt level
- Post-generation validation catches dangerous recommendations
- Maraka planet stones are never recommended
- Safety validation warnings appended to flagged output

See [docs/vedic/GEMSTONE_SAFETY.md](docs/vedic/GEMSTONE_SAFETY.md) for details.

### Computation Integrity

Swiss Ephemeris planetary positions are **never approximated** and cannot be
overridden by LLM output or Pandit Ji corrections. The 6-layer validation
pipeline (Layer 1: Astronomical Fact Check) auto-rejects any correction that
contradicts computed positions.

### Data Privacy

- Birth data (name, DOB, TOB, place) is processed locally
- No data is sent to external services except the configured LLM backend
- Pandit Ji corrections are stored as local JSON files
- No telemetry or analytics are collected
