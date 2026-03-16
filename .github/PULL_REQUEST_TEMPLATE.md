## Summary

<!-- 1-3 bullet points describing what this PR does and why -->

-

## Type of Change

- [ ] `feat` — New feature
- [ ] `fix` — Bug fix
- [ ] `safety` — Gemstone/interpretation safety fix
- [ ] `refactor` — Code restructuring (no behavior change)
- [ ] `docs` — Documentation only
- [ ] `test` — Adding or updating tests
- [ ] `chore` — Build, CI, tooling

## Checklist

### Code Quality
- [ ] `make lint` passes with no errors
- [ ] `make typecheck` passes
- [ ] `make test` — all tests pass
- [ ] No file exceeds 300 lines
- [ ] All new functions have type hints and docstrings
- [ ] No magic numbers — constants in `domain/constants/` or `knowledge/`

### Architecture
- [ ] Dependencies flow inward (deliver → interpret → compute)
- [ ] No LLM calls in `compute/` layer
- [ ] New data structures use `@dataclass`, not raw dicts
- [ ] Configuration via `config.yaml`, not hardcoded values

### Vedic Safety (if touching interpret/ or knowledge/)
- [ ] Gemstone recommendations checked against lordship rules
- [ ] Maraka planets acknowledged with dual-nature description
- [ ] Prompt templates inject lordship rules + prohibited stones
- [ ] Post-generation validation catches dangerous recommendations
- [ ] `make safety-check` passes

### Testing
- [ ] Added/updated tests for new behavior
- [ ] Safety-critical changes have explicit test coverage
- [ ] Tested with reference chart (Manish 13/03/1989 12:17 Varanasi)

## Test Plan

<!-- How to verify this change works correctly -->

-

## Related Issues

<!-- Link to related issues: Fixes #123, Relates to #456 -->
