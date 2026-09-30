from dataclasses import dataclass
from datetime import date

import pytest

from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.base import DTOError, SchemaError, SerializationError
from django_dto_field.storage.binary import BinaryStorage
from django_dto_field.storage.json import JSONStorage
from django_dto_field.storage.text import TextStorage


@dataclass
class Address:
    city: str


@dataclass
class Person:
    name: str
    address: Address
    birthday: date


def test_nested_dataclass_round_trip():
    converter = DTOConverter(Person)
    person = Person("Ada", Address("London"), date(1815, 12, 10))
    data = converter.to_data(person)
    assert data == {
        "name": "Ada",
        "address": {"city": "London"},
        "birthday": "1815-12-10",
    }
    assert converter.from_data(data) == person


def test_dict_round_trip():
    converter = DTOConverter(dict)
    data = {"unicode": "Привет", "nested": [1, None, False, {"a": 1.5}]}
    assert converter.from_data(converter.to_data(data)) == data


@pytest.mark.parametrize(
    "schema", [str, list, object, Person("a", Address("b"), date.today())]
)
def test_unsupported_schema(schema):
    with pytest.raises(SchemaError):
        DTOConverter(schema)


@pytest.mark.parametrize(
    "data",
    [[], "text", 1, {"name": "Ada"}, {"name": 123, "address": {}, "birthday": "bad"}],
)
def test_invalid_dataclass_data(data):
    with pytest.raises(DTOError):
        DTOConverter(Person).from_data(data)


@pytest.mark.parametrize("data", [object(), Person(1, Address("Paris"), date.today())])
def test_invalid_dataclass_instance(data):
    with pytest.raises(DTOError):
        DTOConverter(Person).to_data(data)


def test_unserializable_dict_has_library_exception():
    with pytest.raises(SerializationError) as error:
        DTOConverter(dict).to_data({"bad": object()})
    assert error.value.__cause__ is not None


@pytest.mark.parametrize(
    "storage, expected",
    [
        (TextStorage(), '{"a":1}'),
        (BinaryStorage(), b'{"a":1}'),
        (JSONStorage(), {"a": 1}),
    ],
)
def test_storage_uses_native_field_values(storage, expected):
    assert storage.encode({"a": 1}) == expected
    assert storage.decode(expected) == {"a": 1}


@pytest.mark.parametrize(
    "raw", [b'{"a":1}', bytearray(b'{"a":1}'), memoryview(b'{"a":1}'), '{"a":1}']
)
def test_binary_driver_representations(raw):
    assert BinaryStorage().decode(raw) == {"a": 1}


@pytest.mark.parametrize("raw", [b"bad", b"\xff", object()])
def test_malformed_storage(raw):
    with pytest.raises(SerializationError):
        BinaryStorage().decode(raw)


def test_storage_encoding_errors_are_library_exceptions():
    with pytest.raises(SerializationError) as error:
        BinaryStorage().encode({"bad": object()})
    assert isinstance(error.value.__cause__, TypeError)
