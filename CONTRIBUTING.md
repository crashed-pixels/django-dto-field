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
*   `make test` includes unit and Django E2E tests using in-memory SQLite by default, with settings and import paths configured in `pyproject.toml`.
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
| `make e2e` | Run Django E2E tests on the selected database (SQLite by default). |
| `make typing` | Run strict `mypy` type checks on the `src` directory. |
| `make lint` | Run Ruff lint/format checks on source and tests, and WPS checks on source. |
| `make format` | Auto-fix imports (`ruff`) and format code (`ruff format`). |
| `make all-checks` | Clean caches and run linting, typing, and tests (Recommended before PR). |

The E2E test app is unmigrated: Django creates its tables from the current
models when pytest sets up the test database. Changes to test models do not
require generating migration files.

### E2E tests on SQL databases

Django supports SQLite, PostgreSQL, MySQL, MariaDB, and Oracle. `make test` runs
the entire suite on SQLite without Docker. To run the E2E suite on another backend,
start its Docker Compose service, install the corresponding test driver, and set
`DTO_TEST_DB`:

| `DTO_TEST_DB` | Compose service | Driver group | Local port |
| :--- | :--- | :--- | ---: |
| `postgresql` | `postgresql` | `dev` (already installed) | 55432 |
| `mysql` | `mysql` | `mysql` | 53306 |
| `mariadb` | `mariadb` | `mysql` | 53307 |
| `oracle` | `oracle` | `oracle` | 51521 |

For example:

```bash
docker compose --profile postgresql up -d --wait postgresql
DTO_TEST_DB=postgresql make e2e
docker compose --profile postgresql down -v
```

For MySQL and MariaDB, install the MySQL client development libraries first
(for example, `brew install mysql-client pkg-config` on macOS or
`sudo apt-get install default-libmysqlclient-dev pkg-config` on Ubuntu), then
run `uv sync --group mysql`. For Oracle, run `uv sync --group oracle`; the
`oracledb` thin driver needs no Oracle client installation. PostgreSQL uses the
driver from the default dev dependencies. Substitute the backend name in the
Compose and `make e2e` commands above. Allow at least 4 GB of memory for
Docker when running Oracle; its image may take longer to start on the first run.

`DTO_TEST_DB_HOST`, `DTO_TEST_DB_PORT`, `DTO_TEST_DB_NAME`, `DTO_TEST_DB_USER`,
and `DTO_TEST_DB_PASSWORD` override the test settings for an external server.
The Compose credentials are for disposable local databases only. Django creates
and destroys an isolated test database (or test user and tablespace for Oracle)
on every run.

### Python, Django, and database matrix

CI runs tox for each supported Python × Django × database combination. SQLite
environments run the entire suite with 100% source coverage; server database
environments run the E2E suite. The Django versions are 4.2, 5.2, 6.0, and 6.1.
Python 3.10–3.11 run Django 4.2/5.2, Python 3.12 runs all four, and Python
3.13–3.14 run Django 5.2/6.0/6.1.

Run the default SQLite environment locally with `uvx --with tox-uv tox`. To
select a combination, use `py<version>-django<version>-<database>`:

```bash
uvx --with tox-uv tox -e py312-django52-sqlite
docker compose --profile postgresql up -d --wait postgresql
uvx --with tox-uv tox -e py312-django52-postgresql
docker compose --profile postgresql down -v
```

Install other Python versions with `uv python install 3.10 3.11 3.12 3.13 3.14`.
For MySQL/MariaDB, the same system client libraries are required for tox as
for `make e2e`. On macOS, set
`PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"` when invoking
tox so it can compile `mysqlclient`. Oracle uses the pure-Python `oracledb`
thin client. tox installs the appropriate Django and database driver into
each environment independently of `uv.lock`.

JSON `__in` lookups are expected to fail on MySQL/MariaDB with Django versions
before 6.1: those Django backends compare JSON values against text in that
lookup. Exact JSON lookups remain covered.

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
