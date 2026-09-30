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
    """A Django JSONField with DTO mixin.

    Because Django JSONFiled provides lookups we must support them for DTO's object.
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
        # NOTE: Lookup RHS values may be JSON scalars or partial objects, not full DTOs.
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
            # NOTE: Keep Value(None) intact: JSON null is distinct from SQL NULL.
            if prepared.value is not None:
                prepared = prepared.value
        if not hasattr(prepared, "resolve_expression"):
            prepared = self._prepare(prepared)
        return super().get_db_prep_save(prepared, connection)
