"""Exercise application reports, expression writes, and native JSON semantics."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, models
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from dict_field.models import (
    Address,
    Customer,
    DictModel,
    NativeJSONModel,
    NullableModel,
    Order,
    UserDTO,
)

pytestmark = pytest.mark.django_db


def test_search_combines_nested_ranges_list_indexes_and_exclusions(order):
    found = Order.objects.filter(
        Q(snapshot__items__0__quantity__gte=2) & Q(snapshot__customer="Alice")
    ).exclude(snapshot__items__0__sku="missing")
    assert found.get() == order
    assert not Order.objects.filter(snapshot__missing__isnull=False).exists()
    assert Order.objects.filter(snapshot__has_key="items").get() == order


def test_values_distinguishes_whole_dto_from_native_projections(order):
    row = Order.objects.values(
        "snapshot", "snapshot__items", "snapshot__items__0__quantity"
    ).get()
    assert row == {
        "snapshot": order.snapshot,
        "snapshot__items": [{"sku": "book", "quantity": 2}],
        "snapshot__items__0__quantity": 2,
    }


def test_ordering_grouping_and_aggregation_use_native_output_types():
    for category, quantity in [("book", 2), ("book", 3), ("game", 1)]:
        DictModel.objects.create(json={"category": category, "quantity": quantity})
    reports = DictModel.objects.annotate(
        category=KeyTextTransform("category", "json"),
        quantity=Cast(KeyTextTransform("quantity", "json"), models.IntegerField()),
    )
    assert list(reports.order_by("quantity").values_list("quantity", flat=True)) == [
        1,
        2,
        3,
    ]
    assert list(
        reports.values("category")
        .annotate(total=Sum("quantity"), count=Count("pk"))
        .order_by("category")
    ) == [
        {"category": "book", "total": 5, "count": 2},
        {"category": "game", "total": 1, "count": 1},
    ]


@pytest.mark.parametrize(
    "label", ("0", "true", "null", "1.5", 'quote"\\\n', "Привет 🌍")
)
def test_scalar_looking_strings_remain_strings(label):
    instance = DictModel.objects.create(json={"label": label})
    instance.refresh_from_db()
    assert instance.json == {"label": label}
    assert (
        DictModel.objects.annotate(label=KeyTextTransform("label", "json"))
        .values_list("label", flat=True)
        .get(pk=instance.pk)
        == label
    )


@pytest.mark.parametrize("label", ("0", "true", "null", "1.5"))
def test_key_projection_retains_native_django_backend_behavior(label):
    instance = DictModel.objects.create(json={"label": label})
    native = NativeJSONModel.objects.create(payload={"label": label})
    actual = DictModel.objects.values_list("json__label", flat=True).get(pk=instance.pk)
    expected = NativeJSONModel.objects.values_list("payload__label", flat=True).get(
        pk=native.pk
    )
    assert type(actual) is type(expected)
    assert actual == expected


def test_json_containment_accepts_partial_mapping(order):
    if not connection.features.supports_json_field_contains:
        pytest.skip("Backend does not support JSON containment")
    assert Order.objects.filter(snapshot__contains={"customer": "Alice"}).get() == order


@pytest.mark.parametrize("field_name", ("snapshot", "text", "binary"))
def test_instance_f_expression_survives_save_and_refresh(order, field_name):
    before = getattr(order, field_name)
    setattr(order, field_name, F(field_name))
    order.save(update_fields=[field_name])
    order.refresh_from_db()
    assert getattr(order, field_name) == before


def test_case_expression_selects_valid_snapshot(order, snapshot):
    snapshot.note = "paid gift"
    field = Order._meta.get_field("snapshot")
    Order.objects.update(
        snapshot=Case(
            When(pk=order.pk, then=Value(snapshot, output_field=field)),
            default=F("snapshot"),
            output_field=field,
        )
    )
    order.refresh_from_db()
    assert order.snapshot.note == "paid gift"


def test_compatible_field_copy_converts_on_load(order):
    Order.objects.update(archived_snapshot=F("snapshot"))
    order.refresh_from_db()
    assert order.archived_snapshot == order.snapshot


def test_subquery_with_dto_output_field_reconstructs_snapshot(order):
    subquery = (
        Order.objects.filter(customer_id=OuterRef("pk"))
        .order_by("pk")
        .values("snapshot")[:1]
    )
    customer = Customer.objects.annotate(
        latest_snapshot=Subquery(
            subquery, output_field=Order._meta.get_field("snapshot")
        )
    ).get(pk=order.customer_id)
    assert customer.latest_snapshot == order.snapshot


def test_expression_result_is_validated_when_loaded():
    instance = DictModel.objects.create(json={"identifier": "bad"})
    field = NullableModel._meta.get_field("json")
    with pytest.raises(ValidationError):
        DictModel.objects.annotate(dto=Cast("json", field)).values_list(
            "dto", flat=True
        ).get(pk=instance.pk)


def test_sql_null_json_null_empty_and_null_member_are_distinct():
    field = NullableModel._meta.get_field("json")
    sql_null = NullableModel.objects.create(json=None)
    json_null = NullableModel.objects.create(json=Value(None, output_field=field))
    empty = DictModel.objects.create(json={})
    member = DictModel.objects.create(json={"note": None})
    assert set(
        NullableModel.objects.filter(json__isnull=True).values_list("pk", flat=True)
    ) == {sql_null.pk}
    assert set(
        NullableModel.objects.filter(json__isnull=False).values_list("pk", flat=True)
    ) == {json_null.pk}
    assert DictModel.objects.filter(json__note__isnull=True).get() == empty
    assert DictModel.objects.filter(json__has_key="note").get() == member
    assert DictModel.objects.get(pk=empty.pk).json == {}
    assert DictModel.objects.get(pk=member.pk).json == {"note": None}


def test_populated_nullable_dto_can_be_cleared_and_restored():
    payload = UserDTO(1, Address("London"))
    instance = NullableModel.objects.create(json=payload)
    instance.json = None
    instance.save(update_fields=["json"])
    instance.refresh_from_db()
    assert instance.json is None
    instance.json = payload
    instance.save(update_fields=["json"])
    instance.refresh_from_db()
    assert instance.json == payload
