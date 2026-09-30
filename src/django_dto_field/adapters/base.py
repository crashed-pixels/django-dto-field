"""Define the schema-neutral :class:`DTOAdapter` extension protocol."""

from abc import abstractmethod
from typing import Any, Protocol, TypeGuard, TypeVar

DTO = TypeVar("DTO")


class DTOAdapter(Protocol[DTO]):
    """Adapt a schema to DTO instances and JSON-compatible mappings.

    :param schema: Importable schema class supported by the implementation.

    The schema class need not be the returned DTO's class. Implementations
    translate their library's errors to
    :class:`~django_dto_field.exceptions.base.DTOError` subclasses and are instantiated
    per converter, never registered globally.
    """

    @abstractmethod
    def __init__(self, schema: type[Any]) -> None:
        """Configure the schema supported by this adapter.

        :param schema: Importable schema class.
        :raises ~django_dto_field.exceptions.base.SchemaError: If unsupported.
        """

    @abstractmethod
    def is_instance(self, instance: object) -> TypeGuard[DTO]:
        """Recognize DTO instances without validating their member values."""

    @abstractmethod
    def to_data(self, instance: DTO) -> dict[str, Any]:
        """Dump an instance to a JSON-compatible object, not encoded JSON.

        :param instance: DTO recognized by ``is_instance()``.
        :returns: A mapping containing JSON-compatible values.
        :raises ~django_dto_field.exceptions.base.SerializationError: If dumping fails.
        """

    @abstractmethod
    def from_data(self, payload: dict[str, Any]) -> DTO:
        """Validate a complete object and reconstruct its DTO instance.

        :param payload: Complete JSON-compatible mapping to validate.
        :returns: Validated DTO; its class need not match the schema class.
        :raises ~django_dto_field.exceptions.base.DTOValidationError: If invalid.
        """
