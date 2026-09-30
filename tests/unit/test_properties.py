"""Exercise recursive JSON values and typed DTOs across storage representations."""

from dataclasses import dataclass
from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.base import DTOValidationError
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.char import DTOCharField
from django_dto_field.fields.json import DTOJSONField
from django_dto_field.storage.binary import BinaryStorage
from django_dto_field.storage.json import JSONStorage
from django_dto_field.storage.text import TextStorage

TEXT = st.text(alphabet=st.characters(exclude_categories=("Cs",)), max_size=40)
SCALARS = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**63), max_value=2**63 - 1),
    st.floats(allow_nan=False, allow_infinity=False),
    TEXT,
)
JSON_VALUES = st.recursive(
    SCALARS,
    lambda children: st.one_of(
        st.lists(children, max_size=5), st.dictionaries(TEXT, children, max_size=5)
    ),
    max_leaves=20,
)
JSON_OBJECTS = st.dictionaries(TEXT, JSON_VALUES, max_size=5)


@dataclass
class Event:
    """A typed DTO containing temporal data and nested sequences."""

    identifier: int
    label: str
    occurred_on: date
    tags: list[str]


@given(JSON_OBJECTS)
def test_recursive_json_round_trip_across_every_storage(payload):
    converter = DTOConverter(dict)
    for storage in [TextStorage(), BinaryStorage(), JSONStorage()]:
        restored = converter.from_data(
            storage.decode(storage.encode(converter.to_data(payload)))
        )
        assert restored == payload


@given(st.builds(Event, st.integers(), TEXT, st.dates(), st.lists(TEXT, max_size=5)))
def test_dataclass_field_round_trip_and_identity(event):
    for field_class in [DTOCharField, DTOBinaryField, DTOJSONField]:
        field = field_class(schema=Event)
        assert field.to_python(event) is event
        prepared = field.get_prep_value(event)
        # JSON database decoding is handled by Django; other codecs decode here.
        assert field.to_python(prepared) == event


@given(st.one_of(st.none(), st.booleans(), TEXT, st.lists(SCALARS, max_size=3)))
def test_invalid_member_types_are_rejected_before_storage(identifier):
    event = Event(identifier, "test", date(2026, 1, 1), [])
    with pytest.raises(DTOValidationError):
        DTOConverter(Event).to_data(event)


@given(JSON_OBJECTS)
def test_binary_codec_handles_all_database_buffer_types(payload):
    storage = BinaryStorage()
    encoded = storage.encode(payload)
    for raw in [
        encoded,
        bytearray(encoded),
        memoryview(encoded),
        encoded.decode("utf-8"),
    ]:
        assert storage.decode(raw) == payload
