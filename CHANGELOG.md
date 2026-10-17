# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] 2026-10-17

### Added

- README documentation for user-defined adapters, including their advantages, limitations, and a practical use case.

### Fixed

- Report descriptive error message mentioning expected and given DTO types when a mismatched dataclass instance is provided to DTO fields (#58).

## [1.0.0] 2026-10-11

### Added

- Contributor Covenant 2.1 `CODE_OF_CONDUCT.md` with a private reporting contact and a link from the contribution guide.
- A README comparison of Django's `JSONField` and `DTOField` using the same nested dataclasses, showing automatic conversion, schema validation, and JSON lookups.
- A README table of contents and a monthly PyPI downloads badge.
- Regression tests for the renamed field's migration import path and the removal of the character-field module.

### Changed

- **Breaking:** rename the JSON-backed `DTOJSONField` to `DTOField`, imported from `django_dto_field.fields.json`. Native JSON storage and field behavior are unchanged. The old name is removed; application imports and historical migration references must be updated.
- Reorganize the README around practical examples, supported DTO types, and the two remaining model fields, replacing the feature checklist and clarifying when plain `JSONField` may be preferable.
- Update unit, property-based, and Django E2E tests for JSON and binary fields after removing character-field support.
- Clarify contribution and repository guidance for dependency installation, linting, coverage exclusions, supported Python/Django combinations, CI triggers, and database test setup.

### Fixed

- Correct missing imports and undefined variables in README examples, and clarify dictionary validation, assignment validation, and optional form input.
- Fix README badge links, labels, and HTML nesting; load the logo from GitHub so it also displays on PyPI, and update repository links to `crashed-pixels/django-dto-field`.
- Synchronize the editable package version in `uv.lock` with the declared `0.2.0` version.

### Removed

- **Breaking:** remove `DTOCharField` and its `TextStorage` implementation. Supported DTO model fields are now `DTOField` and `DTOBinaryField`; imports of the removed field in application code or historical migrations must be updated.

## [0.2.0] 2026-10-09

### Added

- `validate_on_assignment=False` to disable assignment validation; migrations preserve the option.
- Realistic Django E2E scenarios covering partial saves, deferred loading, transactions, bulk imports/upserts, JSON queries, relationships, forms, HTTP/admin requests, fixtures, historical models, and schema evolution.
- Property-based tests for rich DTOs, repeated nested edits, and adapters returning dictionaries.
- PostgreSQL, MySQL, and MariaDB test environments with Docker Compose, tox, and `make e2e`.

### Changed

- **Breaking:** all DTO fields validate schema values on assignment and model construction by default. Failed assignments preserve the previous value; Django field validators still require `full_clean()`.
- **Breaking:** raise the minimum Django version from 4.2 to 5.2.
- Run 10 representative CI test environments across Python 3.10–3.14, Django 5.2/6.0/6.1, and four database backends; cancel superseded runs.
- Create E2E test tables from current models instead of checked-in test-app migrations.
- Expand README examples and contribution guidance with field restrictions, default dictionary behavior, supported versions, and database test setup.

### Fixed

- Report ModelForm schema validation errors on the affected field instead of as form-wide errors.

## [0.1.0] - 2026-10-01

### Added

- `DTOCharField`, `DTOBinaryField`, and `DTOJSONField` with a shared Django lifecycle mixin.
- Explicit schema conversion, nested dataclass/member validation, and JSON ModelForm support.
- An explicit `DTOAdapter` protocol and per-field `adapter=` selection for future third-party integrations. Schema classes and DTO result types are independent; migrations preserve the adapter class. No third-party integrations or dependencies are added.
- A common `DTOError` hierarchy with Django-compatible `DTOFieldError` boundary translation.
- Replacement unit and Django E2E tests covering CRUD, bulk operations, expressions, JSON lookups, forms, migrations, fixtures, and malformed input.

### Changed

- **Breaking:** store native JSON text, bytes, or mappings instead of framed binary data. The current API does not support prerelease storage formats or imports.
- Organize conversion, storage, model fields, form fields, and exceptions into separate packages.
- Require strict mypy and 100% statement/branch coverage. Ruff now checks and formats source and tests.

### Removed

- The old `DTOField`, global DTO registry, `HandlerDTO`, and `BinaryDTOParser`.
- The stale benchmark target referencing a missing management command.

## [0.1.1-beta1] - 2026-07-08

### Added

- Migrate from `poetry` to `uv`. 
- `CONTRIBUTING.md` for new contributions.

## [0.1.0-beta1] - 2026-05-11

### Added

- Add benchmarks `JSONField` vs `DTOField`, #26

## [0.1.0-alpha3] - 2026-05-03

### Added

- Add `dataclass` support, #29

### Changed

- Move `dto_code` checking to `BaseDtoFeature` class.
- Breaking: change `DtoField` naming to `DTOField` to be similar to `JSONField` naming.

### Removed

- Registry class because of it over-engineering propose.
- `TypedDict` support because of int not DTO nature, #28

## [0.1.0-alpha2] - 2026-04-05

### Changed

- Structure and naming, #23

### Added

- More unit tests during architecture changing.
- Binary DTO's now storing with TLV (Type-Length-Value).
- Global registry for serialization information storage.

## [0.1.0-alpha1] - 2026-01-26

### Added

- Serialization and deserialization dict field values, #13 #14
