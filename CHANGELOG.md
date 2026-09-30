# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
