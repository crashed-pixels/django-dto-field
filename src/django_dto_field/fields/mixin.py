from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Generic

from django import forms
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper

from django_dto_field.adapters import DTOAdapter
from django_dto_field.adapters.base import DTO
from django_dto_field.conversion import DTOConverter
from django_dto_field.exceptions import DTOFieldError
from django_dto_field.exceptions.django import field_errors
from django_dto_field.forms import DTOFormField
from django_dto_field.storage import JSONStorage

if TYPE_CHECKING:
    Field = models.Field[Any, Any]
else:
    Field = models.Field


class DTOFieldMixin(Field, Generic[DTO]):  # noqa: WPS214
    """Core logic for handling DTOs in Django fields.

    This class mixin must be used in conjunction with a Django fields to provide
    seamless integration between DTOs and Django's field system.

    We currently support:
    - :class:`DTOBinaryField` for Django `BinaryField`
    - :class:`DTOCharField` for Django `CharField`
    - :class:`DTOJSONField` for Django `JSONField`

    Schema
    ------

    While using a `DTO<your-choice>Field` you can provide two optional
    key-value args. On of it is `schema`.

    By setting `schema` you can specify the schema of your DTO object for validation
    and working with it out-of-the-box with Django field.

    By default schema is not set and you will work with `dict` object.

    We currently support:
    - `dataclass` for dataclasses objects

    Adapter
    -------

    The second optional key-value arg is `adapter`.

    The :class:`DTOAdapter` allows you to specify a validation and conversion strategy
    for your type of DTO.

    If you use supported DTO types, it is better to use builtin adapters. They will
    be selected based on the provided DTO type.

    We currently support:
    - :class:`MsgspecAdapter` for `dict` and `dataclass` DTO's

    Convertor
    ---------

    After defining schema and adapter, the :class:`DTOConverter` will be used in Django field
    to handle the conversion between the DTO and its database representation.

    Let's say you have this DTO dataclass:

    >>> from dataclasses import dataclass

    >>> @dataclass
    >>> class Address:
    ...     city: str

    >>> @dataclass
    >>> class Customer:
    ...     name: str
    ...     address: Address

    And define Django model like this:

    >>> from django.db import models
    >>> class MyModel(models.Model):
    ...     customer = DTOJSONField(schema=Customer)

    Now you trying to save model:

    >>> order = Order.objects.create(
    ...     customer=Customer(
    ...         name="Alice",
    ...         address=Address(city="London"),
    ...     )
    ... )

    During the save, converter will:
    1. Using adapter asks is the value recognized DTO.
    2. Converting DTO to `dict`.
    3. Validate the `dict` through the adapter before storage.

    The converter coordinates conversion and validation; it does not write
    to the database. For this field use storage class variable.

    Storage
    -------

    Basic usage of mixin is:

    >>> from django.db.models import CharField
    >>> class MyDTOField(DTOFieldMixin, CharField):
    ...     storage = TextStorage()

    By default all DTO's converts to JSON compatible format using :class:`JSONStorage`. But
    for the other fields we must create a adapter to storing DTO in correct format for Django.

    Here is current adapters:
    - :class:`JSONStorage` for :class:`DTOJSONField` (basic and default)
    - :class:`TextStorage` for :class:`DTOCharField`
    - :class:`BinaryStorage` for :class:`DTOBinaryField`
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
