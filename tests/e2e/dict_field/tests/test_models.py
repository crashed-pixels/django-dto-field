"""Exercise rich DTO types, relationships, inheritance, and snapshots."""

from datetime import date, datetime
from uuid import UUID

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from dict_field.models import Customer, DictModel, Order, OrderProxy
from dict_field.schemas import Delivery, LineItem

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("field_name", ("snapshot", "text", "binary"))
def test_rich_snapshot_restores_member_types(order, field_name):
    order.refresh_from_db()
    snapshot = getattr(order, field_name)
    assert isinstance(snapshot.reference, UUID)
    assert isinstance(snapshot.placed_at, datetime)
    assert snapshot.placed_at.utcoffset().total_seconds() == 0
    assert type(snapshot.delivery_on) is date
    assert snapshot.delivery is Delivery.STANDARD
    assert isinstance(snapshot.items[0], LineItem)


def test_frozen_slotted_line_item_survives_edit(order):
    order.snapshot.items.append(LineItem("gift", 1))
    order.save(update_fields=["snapshot"])
    order.refresh_from_db()
    assert order.snapshot.items == [LineItem("book", 2), LineItem("gift", 1)]
    assert not hasattr(order.snapshot.items[0], "__dict__")


def test_select_related_loads_customer_and_snapshot_in_one_query(
    order, django_assert_num_queries
):
    with django_assert_num_queries(1):
        loaded = Order.objects.select_related("customer").get(pk=order.pk)
        assert loaded.customer.name == loaded.snapshot.customer == "Alice"


def test_prefetch_related_loads_order_snapshots_without_extra_queries(
    order, django_assert_num_queries
):
    with django_assert_num_queries(2):
        customer = Customer.objects.prefetch_related("orders").get(pk=order.customer_id)
        assert [related.snapshot for related in customer.orders.all()] == [
            order.snapshot
        ]


def test_snapshot_does_not_follow_customer_rename(order):
    order.customer.name = "Renamed"
    order.customer.save(update_fields=["name"])
    order.refresh_from_db()
    assert (order.customer.name, order.snapshot.customer) == ("Renamed", "Alice")


def test_abstract_field_and_proxy_keep_assignment_validation(order):
    proxy = OrderProxy.objects.get(pk=order.pk)
    with pytest.raises(ValidationError):
        proxy.snapshot = {"customer": 123}
    proxy.snapshot.note = "proxy edit"
    proxy.save(update_fields=["snapshot"])
    order.refresh_from_db()
    assert order.snapshot.note == "proxy edit"


@pytest.mark.parametrize("field_name", ("text", "binary", "json"))
def test_json_numeric_and_unicode_boundaries_survive_storage(field_name):
    payload = {
        "low": -(2**63),
        "high": 2**63 - 1,
        "fraction": 0.125,
        "label": 'Привет 🌍\n"\\',
    }
    instance = DictModel.objects.create(**{field_name: payload})
    instance.refresh_from_db()
    assert getattr(instance, field_name) == payload


@pytest.mark.parametrize("field_name", ("snapshot", "text", "binary"))
def test_invalid_line_item_member_is_rejected_on_save(order, field_name):
    getattr(order, field_name).items.append(LineItem("bad", "many"))
    with pytest.raises(ValidationError), transaction.atomic():
        order.save(update_fields=[field_name])
    order.refresh_from_db()
    assert getattr(order, field_name).items == [LineItem("book", 2)]
