# Release Checklist

## Pre-release checks

1. Run `uv run ruff check .`
2. Run `uv run ruff format --check .`
3. Run `uv run mypy`
4. Run `uv run pytest`
5. Review [`.env.prod.example`](../.env.prod.example)
6. Review [`deploy/systemd/`](../deploy/systemd/)
7. Review [`README.md`](../README.md) and the docs for command or settings drift
8. Confirm public metadata in [`pyproject.toml`](../pyproject.toml) is still accurate
9. Confirm community health files are present and aligned:
   - [`CONTRIBUTING.md`](../CONTRIBUTING.md)
   - [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md)
   - [`SECURITY.md`](../SECURITY.md)

## Publish checks

1. Confirm the CI workflow in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
   is green
2. Confirm docs do not contain private filesystem paths
3. Confirm env examples contain blank secret placeholders
4. Confirm the repository tree is clean and free of `__pycache__` and `*.pyc`

## Post-publish verification

1. Clone the repository into a fresh directory
2. Run `uv sync --group dev`
3. Run `uv run mail-rbl-monitor --dry-run`
4. Run `uv run mail-rbl-monitor --dry-run --json`
5. Confirm the docs, systemd templates, and env examples match the cloned repository
