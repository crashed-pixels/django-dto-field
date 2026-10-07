# Contributing to `django-dto-field`

Thank you for your interest in contributing! This document provides guidelines and instructions to help you get started.

## Project Overview

`django-dto-field` provides `DTOCharField`, `DTOBinaryField`, and `DTOJSONField` for storing dictionaries and typed dataclasses using native Django storage representations.

**Core Tech Stack:**
*   **Python:** 3.10 - 3.14
*   **Framework:** Django >= 4.2.0
*   **Serialization:** `msgspec` (for high-performance encoding/decoding)
*   **Build & Package Management:** `uv`

## Getting Started

We use `uv` for dependency management and virtual environments.

1.  **Install `uv`** (if you haven't already):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Install dependencies:**
    ```bash
    uv sync
    ```
    *(Note: `uv sync` automatically installs all dev dependencies and sets up the virtual environment based on `uv.lock`).*

## Code Quality & Standards

We maintain strict code quality standards. CI will fail if any of the following are not met:

### 1. 100% Test Coverage
We require **100% statement and branch coverage** for all new and existing runtime code. Type-checking-only imports are excluded from runtime coverage.
*   Tests are written using `pytest`, `pytest-django`, and `hypothesis`.
*   Use Hypothesis for properties such as storage round trips and recursive JSON values. Keep ORM example counts bounded; do not suppress health checks to work around shared fixture state.
*   Coverage is enforced via `pytest-cov`.
*   If you add a new feature or fix a bug, you **must** write tests for it. Run with `make test`.
*   Use TDD: add a test describing the behavior, observe its failure, then implement and refactor with the tests passing.
*   `make test` includes unit and Django E2E tests. E2E uses in-memory SQLite, with settings and import paths configured in `pyproject.toml`.
*   For a focused suite: `uv run pytest -n 0 --no-cov tests/unit/test_conversion.py`. The default pytest invocation uses parallel workers and enforces coverage over the entire library.

### 2. Strict Typing
*   We use `mypy` in **strict mode** with `django-stubs` for static type checking of `src/`.
*   All public APIs and complex internal logic must be fully typed.
*   Run `make typing` to verify your types before committing.

### 3. Linting and Formatting
We use a hybrid approach for linting to ensure both modern formatting and strict architectural rules:
*   **Ruff:** Checks Python errors and imports, and formats both `src/` and `tests/`.
*   **Flake8 + Wemake Python Styleguide (WPS):** Checks `src/` with WPS rules. Django override parameter names are retained for keyword compatibility, with narrow inline suppressions where necessary.
*   Package `__init__.py` files contain only docstrings, with no executable code or re-exports. Import classes from concrete modules.
*   Document source modules and classes in reStructuredText for Sphinx. Use literal double backticks, qualified `:class:` references, and `:param:` / `:raises:` fields where useful. `make lint` checks that module, package, and public-class docstrings exist.

Run `make format` to automatically fix formatting and import issues.

## Development Commands

We use a `Makefile` to standardize development workflows. All commands automatically run inside the `uv` virtual environment.

| Command | Description |
| :--- | :--- |
| `make test` | Run all unit and Django E2E tests with statement/branch coverage (alias for `make unit`). |
| `make typing` | Run strict `mypy` type checks on the `src` directory. |
| `make lint` | Run Ruff lint/format checks on source and tests, and WPS checks on source. |
| `make format` | Auto-fix imports (`ruff`) and format code (`ruff format`). |
| `make all-checks` | Clean caches and run linting, typing, and tests (Recommended before PR). |

The E2E test app is unmigrated: Django creates its tables from the current
models when pytest sets up its in-memory test database. Changes to test models
do not require generating migration files.

To exercise a newer Django version without updating the lockfile:

```bash
uv run --with 'django>=5.2,<5.3' pytest -n 0 --no-cov
```

## Submitting a Pull Request

Documentation, tests, bug fixes, and adapter proposals are welcome. For larger
changes, open an [issue](https://github.com/skv0zsneg/django-dto-field/issues) first
to discuss the intended behavior. Bug reports should include a minimal example,
Python and Django versions, and expected versus actual results.

Before opening a PR, please ensure:
1.  Your code passes `make all-checks` locally.
2.  Test coverage remains at 100%.
3.  Commit messages are clear and follow conventional commits (optional but appreciated).
4.  You have updated the documentation/docstrings if you changed public APIs.

Thank you for helping make `django-dto-field` better!
