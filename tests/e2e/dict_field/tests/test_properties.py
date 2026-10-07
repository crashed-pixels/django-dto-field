"""Verify generated payloads through Django persistence and JSON projections."""

import pytest
from django.db import connection
from hypothesis import example, given, settings
from hypothesis import strategies as st

from dict_field.models import Address, DataclassModel, DictModel, UserDTO

TEXT = st.text(
    alphabet=st.characters(exclude_categories=("Cs",), exclude_characters="\x00"),
    max_size=30,
)
JSON_VALUES = st.recursive(
    st.one_of(
        st.none(), st.booleans(), st.integers(min_value=-10000, max_value=10000), TEXT
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=4), st.dictionaries(TEXT, children, max_size=4)
    ),
    max_leaves=12,
)


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@example("")
@given(JSON_VALUES)
def test_generated_json_survives_orm_and_key_projection(nested):
    payload = {"nested": nested}
    instance = DictModel.objects.create(text=payload, binary=payload, json=payload)
    try:
        instance.refresh_from_db()
        assert instance.text == instance.binary == instance.json == payload
        projection = DictModel.objects.values_list("json__nested", flat=True).get(
            pk=instance.pk
        )
        if connection.vendor == "oracle" and nested == "":
            assert projection is None
        else:
            assert projection == nested
    finally:
        instance.delete()


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@example(0, "")
@given(st.integers(min_value=-10000, max_value=10000), TEXT)
def test_generated_dataclass_survives_bulk_insert(identifier, city):
    payload = UserDTO(identifier, Address(city))
    instance = DataclassModel.objects.bulk_create(
        [DataclassModel(pk=1, text=payload, binary=payload, json=payload)]
    )[0]
    try:
        instance.refresh_from_db()
        assert instance.text == instance.binary == instance.json == payload
        found = DataclassModel.objects.filter(
            pk=instance.pk, json__address__city=city
        ).exists()
        assert found is (connection.vendor != "oracle" or city != "")
    finally:
        instance.delete()
