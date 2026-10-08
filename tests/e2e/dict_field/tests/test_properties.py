"""Verify generated payloads through Django persistence and JSON projections."""

from datetime import date, datetime, timezone
from uuid import UUID

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from dict_field.models import (
    Address,
    Customer,
    DataclassModel,
    DictModel,
    MappingModel,
    NativeJSONModel,
    Order,
    UserDTO,
)
from dict_field.schemas import Delivery, LineItem, OrderSnapshot

TEXT = st.text(
    alphabet=st.characters(exclude_categories=("Cs",), exclude_characters="\x00"),
    max_size=30,
)
JSON_VALUES = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-10000, max_value=10000),
        TEXT,
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=4), st.dictionaries(TEXT, children, max_size=4)
    ),
    max_leaves=12,
)


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@example("")
@example("0")
@example("true")
@example("null")
@given(JSON_VALUES)
def test_generated_json_survives_orm_and_key_projection(nested):
    payload = {"nested": nested}
    instance = DictModel.objects.create(text=payload, binary=payload, json=payload)
    native = NativeJSONModel.objects.create(payload=payload)
    try:
        instance.refresh_from_db()
        assert instance.text == instance.binary == instance.json == payload
        projection = DictModel.objects.values_list("json__nested", flat=True).get(
            pk=instance.pk
        )
        native_projection = NativeJSONModel.objects.values_list(
            "payload__nested", flat=True
        ).get(pk=native.pk)
        assert type(projection) is type(native_projection)
        assert projection == native_projection
    finally:
        instance.delete()
        native.delete()


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@example(0, "")
@example(0, "0")
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
        assert found
    finally:
        instance.delete()


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@given(
    TEXT,
    st.lists(
        st.builds(LineItem, TEXT, st.integers(min_value=1, max_value=100)), max_size=4
    ),
    st.sampled_from(list(Delivery)),
)
def test_generated_rich_snapshot_restores_types(customer_name, items, delivery):
    customer = Customer.objects.create(name="Account")
    snapshot = OrderSnapshot(
        customer_name,
        items,
        UUID(int=1),
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        date(2026, 1, 3),
        delivery=delivery,
    )
    instance = Order.objects.create(
        customer=customer, snapshot=snapshot, text=snapshot, binary=snapshot
    )
    try:
        instance.refresh_from_db()
        assert instance.snapshot == instance.text == instance.binary == snapshot
        assert instance.snapshot.delivery is delivery
        assert all(isinstance(item, LineItem) for item in instance.snapshot.items)
    finally:
        instance.delete()
        customer.delete()


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@given(st.lists(TEXT, min_size=1, max_size=4))
def test_generated_repeated_nested_edits_survive_refresh(cities):
    instance = DataclassModel.objects.create(
        **dict.fromkeys(("text", "binary", "json"), UserDTO(1, Address("London")))
    )
    try:
        for city in cities:
            for name in ("text", "binary", "json"):
                getattr(instance, name).address.city = city
            instance.save()
            instance.refresh_from_db()
            assert (
                instance.text
                == instance.binary
                == instance.json
                == UserDTO(1, Address(city))
            )
    finally:
        instance.delete()


@pytest.mark.django_db
@settings(max_examples=30, deadline=None)
@given(st.integers(min_value=1, max_value=10000))
def test_generated_mapping_adapter_round_trip(identifier):
    payload = {"identifier": identifier}
    instance = MappingModel.objects.create(
        **dict.fromkeys(("text", "binary", "json"), payload)
    )
    try:
        instance.refresh_from_db()
        assert instance.text == instance.binary == instance.json == payload
        assert MappingModel.objects.filter(
            pk=instance.pk, json__identifier=identifier
        ).exists()
    finally:
        instance.delete()
