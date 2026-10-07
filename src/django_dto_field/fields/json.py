"""Preserve native Django JSON lookups alongside complete DTO conversion."""

from typing import TYPE_CHECKING, Any

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.fields.json import KeyTransform

from django_dto_field.adapters.base import DTO
from django_dto_field.fields.mixin import DTOFieldMixin
from django_dto_field.storage.json import JSONStorage

if TYPE_CHECKING:
    JSONField = models.JSONField[Any, Any]
else:
    JSONField = models.JSONField


class DTOJSONField(DTOFieldMixin[DTO], JSONField):
    """Combine DTO conversion with Django's native JSON field.

    Whole values are validated using the selected schema. Key lookup operands
    and projections remain native JSON values, without whole-DTO validation.
    SQL NULL and explicit JSON null retain Django's distinct semantics.
    See :class:`~django_dto_field.fields.mixin.DTOFieldMixin` for constructor options.
    """

    storage = JSONStorage()

    def from_db_value(
        self,
        value: Any,  # noqa: WPS110
        expression: Any,
        connection: BaseDatabaseWrapper,
    ) -> Any:
        decoded = JSONField.from_db_value(self, value, expression, connection)
        if isinstance(expression, KeyTransform):
            return decoded
        return self.to_python(decoded)

    def get_prep_value(self, value: Any) -> Any:  # noqa: WPS110
        # Lookup operands may be JSON scalars or partial objects, not full DTOs.
        if not isinstance(value, dict) and self.converter.is_instance(value):
            return self._prepare(value)
        return value

    def get_db_prep_save(
        self,
        value: Any,  # noqa: WPS110
        connection: BaseDatabaseWrapper,
    ) -> Any:
        prepared = value
        if isinstance(prepared, models.Value) and isinstance(
            prepared.output_field, DTOJSONField
        ):
            # Value(None) represents JSON null rather than SQL NULL.
            if prepared.value is not None:
                prepared = prepared.value
        if not hasattr(prepared, "resolve_expression"):
            prepared = self._prepare(prepared)
        return super().get_db_prep_save(prepared, connection)
