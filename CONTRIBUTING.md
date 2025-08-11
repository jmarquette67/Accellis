# Contributing

1. Create a feature branch from `main`.
2. Run linters/tests locally:
   - JS/TS: `npx prettier -w . && npx eslint .`
   - Python: `ruff format . && ruff check . && mypy . && pytest`
3. Open a PR. CI must pass.
