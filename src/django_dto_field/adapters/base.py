from abc import abstractmethod
from typing import Any, Protocol, TypeGuard, TypeVar

DTO = TypeVar("DTO")


class DTOAdapter(Protocol[DTO]):
    """Adapt a schema to DTO instances and JSON-compatible mappings.

    The schema class need not be the returned DTO's class. Implementations
    translate their library's errors to DTOError subclasses and are instantiated
    per converter, never registered globally.
    """

    @abstractmethod
    def __init__(self, schema: type[Any]) -> None:
        """Validate/configure the schema, raising SchemaError if unsupported."""

    @abstractmethod
    def is_instance(self, instance: object) -> TypeGuard[DTO]:
        """Recognize DTO instances without validating their member values."""

    @abstractmethod
    def to_data(self, instance: DTO) -> dict[str, Any]:
        """Dump an instance to a JSON-compatible object, not encoded JSON."""

    @abstractmethod
    def from_data(self, payload: dict[str, Any]) -> DTO:
        """Validate a complete object and reconstruct its DTO instance."""
