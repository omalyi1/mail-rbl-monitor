# Contributing

Thanks for contributing to `mail-rbl-monitor`.

## Local setup

```bash
uv sync --group dev
cp .env.example .env
uv run mail-rbl-monitor --dry-run
```

## Quality checks

Run the full local quality gate before opening a pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

## Coding expectations

- preserve the one-shot CLI architecture unless a design change is discussed explicitly
- keep infrastructure concerns behind typed boundaries
- keep tests deterministic and free of live DNS or HTTP calls
- keep docs and env examples aligned with code
- prefer small, explicit changes over speculative platform features

## Commits and pull requests

- keep pull requests focused and reviewable
- explain user-visible behavior changes and operational impact
- include or update tests when behavior changes
- update documentation when commands, settings, or operator flows change

If you are proposing an architectural change, explain why it still fits the project's
small, deterministic, scheduler-friendly design.
