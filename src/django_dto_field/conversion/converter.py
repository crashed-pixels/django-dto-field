"""Coordinate DTO adapters independently of Django and database storage."""

from typing import Any, Generic, TypeGuard

from django_dto_field.adapters.base import DTO, DTOAdapter
from django_dto_field.adapters.msgspec import MsgspecAdapter
from django_dto_field.exceptions.base import DTOValidationError


class DTOConverter(Generic[DTO]):
    """Enforce common DTO invariants and delegate schema-specific behavior.

    :param schema: Schema class understood by the selected adapter.
    :param adapter: Adapter class; defaults to
        :class:`~django_dto_field.adapters.msgspec.MsgspecAdapter`.

    Dumped mappings are loaded through the adapter before storage to validate
    existing and mutated DTO instances. Database encoding is handled separately.
    """

    def __init__(
        self,
        schema: type[Any],
        *,
        adapter: type[DTOAdapter[DTO]] | None = None,
    ) -> None:
        self.schema = schema
        adapter_class = MsgspecAdapter if adapter is None else adapter
        self._adapter: DTOAdapter[DTO] = adapter_class(schema)

    def is_instance(self, instance: object) -> TypeGuard[DTO]:
        """Recognize a DTO independently of its schema class."""
        return self._adapter.is_instance(instance)

    def to_data(self, instance: object) -> dict[str, Any]:
        """Validate members as well as the outer DTO type before storage."""
        if not self.is_instance(instance):
            raise DTOValidationError(
                "Expected a DTO instance recognized by the adapter."
            )
        payload = self._adapter.to_data(instance)
        self.from_data(payload)
        return payload

    def from_data(self, payload: object) -> DTO:
        """Require an object-shaped payload and delegate schema validation."""
        if not isinstance(payload, dict):
            raise DTOValidationError("DTO data must be a JSON object.")
        return self._adapter.from_data(payload)
