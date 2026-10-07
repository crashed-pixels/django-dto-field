from dataclasses import dataclass
from importlib import import_module

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, models

from django_dto_field.exceptions.base import DTOError
from django_dto_field.exceptions.django import DTOFieldError
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.char import DTOCharField
from django_dto_field.fields.json import DTOJSONField


@dataclass
class User:
    identifier: int


FIELDS = [DTOCharField, DTOBinaryField, DTOJSONField]


@pytest.mark.parametrize(
    "field_class, parent",
    [
        (DTOCharField, models.CharField),
        (DTOBinaryField, models.BinaryField),
        (DTOJSONField, models.JSONField),
    ],
)
def test_native_field_inheritance(field_class, parent):
    field = field_class(max_length=100)
    assert isinstance(field, parent)
    assert field.get_internal_type() == parent.__name__


@pytest.mark.parametrize("field_class", FIELDS)
@pytest.mark.parametrize("schema", [dict, User])
def test_deconstruction_round_trip(field_class, schema):
    field = field_class(schema=schema, null=True, blank=True, max_length=200)
    name, path, args, kwargs = field.deconstruct()
    module, class_name = path.rsplit(".", 1)
    restored = getattr(import_module(module), class_name)(*args, **kwargs)
    assert type(restored) is field_class
    assert restored.schema is schema
    assert restored.null and restored.blank and restored.max_length == 200
    assert name is None


@pytest.mark.parametrize("field_class", FIELDS)
def test_null_and_default_schema(field_class):
    field = field_class(null=True, blank=True)
    assert field.schema is dict
    assert field.to_python(None) is None
    assert field.from_db_value(None, None, connection) is None
    assert field.get_db_prep_save(None, connection) is None
    assert field.clean(None, None) is None


@pytest.mark.parametrize("field_class", FIELDS)
def test_valid_dto_conversion_and_clean(field_class):
    field = field_class(schema=User, max_length=200)
    user = User(1)
    assert field.to_python(user) is user
    assert field.to_python({"identifier": 1}) == user
    assert field.clean(user, None) is user


@pytest.mark.parametrize("field_class", FIELDS)
@pytest.mark.parametrize("invalid", [User("wrong"), {}, object(), [], User])
def test_conversion_rejects_invalid_dto_members_and_shapes(field_class, invalid):
    field = field_class(schema=User)
    with pytest.raises(DTOFieldError) as error:
        field.to_python(invalid)
    assert isinstance(error.value, ValidationError)
    assert isinstance(error.value, DTOError)
    assert isinstance(error.value.__cause__, DTOError)


@pytest.mark.parametrize("field_class", FIELDS)
@pytest.mark.parametrize("value, code", [(None, "null"), ({}, "blank")])
def test_django_null_and_blank_validation(field_class, value, code):
    field = field_class(max_length=200)
    with pytest.raises(ValidationError) as error:
        field.clean(value, None)
    assert error.value.code == code


def test_char_max_length_accepts_exact_serialized_length():
    field = DTOCharField(max_length=7)
    assert field.clean({"a": 1}, None) == {"a": 1}


def test_char_max_length_applies_to_serialized_text():
    field = DTOCharField(max_length=5)
    with pytest.raises(ValidationError, match="at most 5"):
        field.clean({"a": 1}, None)


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField])
@pytest.mark.parametrize("encoded", [b'{"identifier":1}', '{"identifier":1}'])
def test_encoded_values_are_decoded(field_class, encoded):
    field = field_class(schema=User)
    assert field.to_python(encoded) == User(1)


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField])
def test_malformed_json_is_rejected(field_class):
    field = field_class(schema=User)
    with pytest.raises(ValidationError):
        field.to_python("not json")


@pytest.mark.parametrize("field_class", FIELDS)
def test_unsupported_schema_raises_django_error(field_class):
    with pytest.raises(DTOFieldError):
        field_class(schema=str)


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField])
def test_expressions_are_not_serialized(field_class):
    expression = models.F("payload")
    assert field_class().get_prep_value(expression) is expression


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField])
def test_storage_encoding_errors_are_django_errors(field_class):
    with pytest.raises(DTOFieldError):
        field_class().get_prep_value({"invalid_unicode": "\ud800"})


@pytest.mark.parametrize("field_class", FIELDS)
def test_null_value_to_string(field_class):
    field = field_class(null=True)
    field.set_attributes_from_name("payload")
    instance = models.Model.__new__(models.Model)
    instance.payload = None
    assert field.value_to_string(instance) is None
