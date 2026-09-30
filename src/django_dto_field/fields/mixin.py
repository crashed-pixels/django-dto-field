"""Integrate DTO conversion with Django field lifecycle hooks."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Generic

from django import forms
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper

from django_dto_field.adapters.base import DTO, DTOAdapter
from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.django import DTOFieldError, field_errors
from django_dto_field.forms.json import DTOFormField
from django_dto_field.storage.json import JSONStorage

if TYPE_CHECKING:
    Field = models.Field[Any, Any]
else:
    Field = models.Field


class DTOFieldMixin(Field, Generic[DTO]):  # noqa: WPS214
    """Core logic for handling DTOs in Django fields.

    Combine this mixin with a native Django field to validate and convert DTOs.

    :param schema: Importable schema class; defaults to :class:`dict`.
    :param adapter: Importable class implementing
        :class:`~django_dto_field.adapters.base.DTOAdapter`.
    :param args: Positional arguments forwarded to the native Django field.
    :param kwargs: Keyword arguments forwarded to the native Django field.

    Supported fields:

    * :class:`~django_dto_field.fields.binary.DTOBinaryField` for binary columns.
    * :class:`~django_dto_field.fields.char.DTOCharField` for text columns.
    * :class:`~django_dto_field.fields.json.DTOJSONField` for native JSON columns.

    Schema
    ------

    Set ``schema`` to an importable dataclass class for typed validation and
    reconstruction. Without a schema, the field works with dictionaries.
    Schema and adapter classes are preserved in Django migrations.

    Adapter
    -------

    ``adapter`` selects the schema-specific validation and conversion strategy.
    The default is :class:`~django_dto_field.adapters.msgspec.MsgspecAdapter`,
    which handles dictionaries and dataclasses. Custom adapters may return a DTO
    whose class differs from the schema class.

    Converter
    ---------

    :class:`~django_dto_field.conversion.converter.DTOConverter` coordinates
    conversion between DTOs and mappings. Storage handles the native field value.

    Let's say you have this DTO dataclass:

    >>> from dataclasses import dataclass

    >>> @dataclass
    ... class Address:
    ...     city: str

    >>> @dataclass
    ... class Customer:
    ...     name: str
    ...     address: Address

    And define Django model like this:

    >>> from django.db import models
    >>> from django_dto_field.fields.json import DTOJSONField
    >>> class Order(models.Model):
    ...     customer = DTOJSONField(schema=Customer)

    Save an instance after creating the model's database table:

    >>> order = Order.objects.create(
    ...     customer=Customer(
    ...         name="Alice",
    ...         address=Address(city="London"),
    ...     )
    ... )

    During a literal write, the converter:

    #. Recognizes the DTO through its adapter.
    #. Converts the DTO to a JSON-compatible dictionary.
    #. Validates the dictionary through the adapter before storage.

    The converter coordinates conversion and validation; it does not write
    to the database. Assignment alone does not validate. Call ``full_clean()``
    to run Django field validators as well as schema validation.

    Storage
    -------

    Basic usage of mixin is:

    >>> from django.db.models import CharField
    >>> from django_dto_field.storage.text import TextStorage
    >>> class MyDTOField(DTOFieldMixin, CharField):
    ...     storage = TextStorage()

    Storage strategies convert mappings to native Django field values:

    * :class:`~django_dto_field.storage.json.JSONStorage` leaves JSON values native.
    * :class:`~django_dto_field.storage.text.TextStorage` produces JSON text.
    * :class:`~django_dto_field.storage.binary.BinaryStorage` produces JSON bytes.
    """

    empty_strings_allowed = False
    empty_values = models.Field.empty_values
    storage: ClassVar[JSONStorage] = JSONStorage()

    def __init__(
        self,
        *args: Any,
        schema: type[Any] | None = None,
        adapter: type[DTOAdapter[DTO]] | None = None,
        **kwargs: Any,
    ) -> None:
        self.schema = dict if schema is None else schema
        self.adapter = adapter
        with field_errors():
            self.converter: DTOConverter[DTO] = DTOConverter(
                self.schema, adapter=adapter
            )
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        if self.schema is not dict:
            kwargs["schema"] = self.schema
        if self.adapter is not None:
            kwargs["adapter"] = self.adapter
        return name, path, args, kwargs

    def to_python(self, value: Any) -> DTO | None:  # noqa: WPS110
        if value is None:
            return None
        with field_errors():
            if self.converter.is_instance(value):
                self.converter.to_data(value)
                return value
            payload = value if isinstance(value, dict) else self.storage.decode(value)
            return self.converter.from_data(payload)

    def from_db_value(
        self,
        value: Any,  # noqa: WPS110
        expression: Any,
        connection: BaseDatabaseWrapper,
    ) -> DTO | None:
        return self.to_python(value)

    def get_prep_value(self, value: Any) -> Any:  # noqa: WPS110
        if hasattr(value, "resolve_expression"):
            return value
        return self._prepare(value)

    def validate(self, value: Any, model_instance: models.Model | None) -> None:  # noqa: WPS110
        # Validate blank/null/choices on the logical value, not encoded '{}'.
        if value is None and not self.null:
            raise DTOFieldError(self.error_messages["null"], code="null")
        if not self.blank and value in self.empty_values:
            raise DTOFieldError(self.error_messages["blank"], code="blank")
        models.Field.validate(self, value, model_instance)
        self._prepare(value)

    def run_validators(self, value: Any) -> None:  # noqa: WPS110
        super().run_validators(self._prepare(value))

    def value_to_string(self, obj: models.Model) -> Any:  # noqa: WPS110
        instance = self.value_from_object(obj)
        if instance is None:
            return None
        with field_errors():
            return self.converter.to_data(instance)

    def formfield(self, **kwargs: Any) -> forms.Field | None:
        return super().formfield(
            **{"form_class": DTOFormField, "converter": self.converter, **kwargs}
        )

    def _prepare(self, instance: Any) -> object:
        converted = self.to_python(instance)
        if converted is None:
            return None
        with field_errors():
            return self.storage.encode(self.converter.to_data(converted))
