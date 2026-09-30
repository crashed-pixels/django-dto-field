"""Validate dictionaries and nested dataclasses with :mod:`msgspec`."""

from dataclasses import is_dataclass
from typing import Any, Generic, TypeGuard, cast

import msgspec

from django_dto_field.adapters.base import DTO
from django_dto_field.exceptions.base import (
    DTOValidationError,
    SchemaError,
    SerializationError,
)


class MsgspecAdapter(Generic[DTO]):
    """Adapt dictionaries and dataclasses using strict msgspec conversion.

    :param schema: :class:`dict` or an importable dataclass class.
    :raises ~django_dto_field.exceptions.base.SchemaError: If unsupported.

    Dataclass annotations are validated when loading mappings. Dumped values are
    JSON-compatible, including nested dataclasses and supported temporal values.
    """

    def __init__(self, schema: type[DTO]) -> None:
        supported = schema is dict or is_dataclass(schema)
        if not isinstance(schema, type) or not supported:
            raise SchemaError("Schema must be dict or a dataclass class.")
        self.schema = schema

    def is_instance(self, instance: object) -> TypeGuard[DTO]:
        """Recognize an instance of the configured dict or dataclass schema."""
        return isinstance(instance, self.schema)

    def to_data(self, instance: DTO) -> dict[str, Any]:
        """Convert dataclass members to JSON-compatible values."""
        try:
            return cast(dict[str, Any], msgspec.to_builtins(instance, str_keys=True))
        except (TypeError, ValueError, RecursionError) as error:
            raise SerializationError(str(error)) from error

    def from_data(self, payload: dict[str, Any]) -> DTO:
        """Reconstruct nested dataclasses, strictly validating annotations."""
        try:
            return msgspec.convert(payload, type=self.schema, strict=True)
        except (TypeError, ValueError) as error:
            raise DTOValidationError(str(error)) from error
