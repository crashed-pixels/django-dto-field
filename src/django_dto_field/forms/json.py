"""Normalize adapter-backed DTO values for Django JSON forms."""

from typing import Any

from django import forms

from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.django import field_errors


class DTOFormField(forms.JSONField):
    """Render DTO instances as JSON while leaving validation to the model field.

    :param converter: Converter shared with the associated model field.
    :param kwargs: Keyword arguments forwarded to Django's JSON form field.

    Initial values and change detection use adapter recognition, so a schema
    class may differ from the class of the resulting DTO.
    """

    def __init__(self, *, converter: DTOConverter[Any], **kwargs: Any) -> None:
        self.converter = converter
        super().__init__(**kwargs)

    def prepare_value(self, value: Any) -> Any:  # noqa: WPS110
        return super().prepare_value(self._normalize(value))

    def to_python(self, value: Any) -> Any:  # noqa: WPS110
        return super().to_python(self._normalize(value))

    def has_changed(self, initial: Any, data: Any) -> bool:  # noqa: WPS110
        return super().has_changed(self._normalize(initial), data)

    def _normalize(self, instance: Any) -> Any:
        if self.converter.is_instance(instance):
            with field_errors():
                return self.converter.to_data(instance)
        return instance
