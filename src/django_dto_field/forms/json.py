from typing import Any

from django import forms

from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.django import field_errors


class DTOFormField(forms.JSONField):
    """Keep form values as JSON mappings; the model field applies its schema."""

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
