# Repository guidance

## Commands and verification

- Run commands from the repository root. `uv sync` installs the library and dev dependencies; CI tests Python 3.10–3.14.
- `make test` (also `make unit`) runs **all** tests, including Django E2E tests. Pytest defaults to `-n=auto`, HTML coverage output, and 100% statement/branch coverage over `src/`; only `TYPE_CHECKING` blocks are excluded beyond coverage's defaults.
- For a focused test without the whole-library coverage gate or parallel workers: `uv run pytest -n 0 --no-cov tests/unit/test_conversion.py::test_nested_dataclass_round_trip`. Use the same flags with a file or directory for a focused suite.
- `make all-checks` cleans caches/coverage output, then runs lint, typing, and tests. Use TDD for features/fixes: observe a failing behavior test before implementing; maintain 100% coverage (`CONTRIBUTING.md`).
- `make lint` checks Ruff lint/formatting on `src tests`, docstring presence with `ruff check --select D100,D101,D104 src`, and Flake8 **WPS-only** rules on `src`. `make format` fixes Ruff issues/formatting; `make typing` runs strict `mypy src`. Plain `ruff check` does not reproduce the lint target.
- E2E settings are in `tests/e2e/django_app/settings.py`: in-memory SQLite, no external database service. Pytest config supplies `DJANGO_SETTINGS_MODULE=django_app.settings` and adds `src` and `tests/e2e` to the import path.
- The E2E `dict_field` app is unmigrated through `MIGRATION_MODULES` in its test settings. Pytest creates its tables from the current models; do not generate or check in migrations for the test app.
- Test another Django version without changing the lockfile with `uv run --with 'django>=5.2,<5.3' pytest -n 0 --no-cov`.

## Implementation constraints

- Package `__init__.py` files contain docstrings only: no re-exports or executable code (WPS). Import fields from `django_dto_field.fields.char`, `.binary`, or `.json`; use concrete module paths for adapters, conversion, storage, forms, and exceptions too.
- Source modules and classes use reStructuredText docstrings for future Sphinx docs: qualified `:class:` references, double-backtick literals, and parameter/error fields where relevant.
- Hypothesis property suites are `tests/unit/test_properties.py` and `tests/e2e/dict_field/tests/test_properties.py`. ORM properties use `@pytest.mark.django_db`, `max_examples=30`, `deadline=None`, and delete each generated row in `finally`; avoid shared fixture state or suppressing health checks.
- `adapters/` owns schema-specific validation/conversion; `conversion/` enforces common invariants; `storage/` converts mappings to native field values; `fields/` handles Django lifecycle hooks; `forms/` renders DTO initial values as JSON. Keep Django exception translation at the boundary (`exceptions/django.py`); internal exceptions inherit `DTOError`.
- Extend DTO support with an importable `adapter=` class implementing `DTOAdapter`, not a registry or type checks in fields/forms. Schema classes may differ from DTO result classes: use `converter.is_instance()`, not `isinstance(value, schema)`. Preserve adapter classes in `deconstruct()`; JSON lookup mappings must bypass whole-DTO validation even for adapters returning dicts.
- `MsgspecAdapter` is the default for dicts/dataclasses; third-party integrations are extension points, not bundled support. `DTOConverter.to_data()` validates dumped mappings by loading them through the adapter. Keep that step so mutated DTOs are checked. Test-only custom-object and dict-result adapters live in `tests/e2e/dict_field/adapters.py`.
- Dataclasses require an explicit, importable schema; the default is `dict`. `deconstruct()` preserves schema. Validation runs on conversion and literal writes, not attribute assignment; full field validators still require `full_clean()`.
- Validators receive storage values (JSON mapping, text, or bytes); `max_length` measures serialized text/bytes. Saving dictionary input does not replace the in-memory attribute with a DTO; `full_clean()` or `refresh_from_db()` performs that conversion. Binary fields retain Django's `editable=False` default.
- JSON key lookups accept partial/scalar operands and projections return native values. Do not apply whole-DTO validation in `DTOJSONField.get_prep_value()` or to `KeyTransform` results. Preserve the distinction between SQL NULL and `Value(None)` JSON null.
- Django field classes aren't runtime-subscriptable on Django 4.2. The `TYPE_CHECKING` base aliases supply generics to mypy without runtime subscription.

## Documentation

- README describes the current API only; do not add beta/legacy compatibility APIs or upgrade tutorials. Keep practical Django examples, concrete imports, and a link to `CONTRIBUTING.md`. Explain purpose, setup, and help/contribution paths in plain language, following the Open Source Guides.

## Publishing

- `.github/workflows/publish.yml` runs `uv build` and `uv publish` on pushes to `main`, rather than on release tags.
