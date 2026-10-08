"""Exercise DTO rendering and validation in real admin add/change pages."""

import json

import pytest
from django.urls import reverse

from dict_field.models import Order

pytestmark = pytest.mark.django_db


def test_admin_change_renders_snapshot_json(admin_client, order):
    response = admin_client.get(
        reverse("admin:dict_field_order_change", args=[order.pk])
    )
    assert response.status_code == 200
    initial = response.context["adminform"].form["snapshot"].value()
    assert json.loads(initial)["items"] == [{"sku": "book", "quantity": 2}]


def test_admin_add_saves_rich_snapshot(admin_client, order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    response = admin_client.post(
        reverse("admin:dict_field_order_add"),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    assert Order.objects.exclude(pk=order.pk).get().snapshot == order.snapshot


def test_admin_change_saves_valid_dto(admin_client, order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    payload["note"] = "admin edit"
    response = admin_client.post(
        reverse("admin:dict_field_order_change", args=[order.pk]),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.snapshot.note == "admin edit"


def test_admin_change_attaches_schema_error_to_field(admin_client, order):
    response = admin_client.post(
        reverse("admin:dict_field_order_change", args=[order.pk]),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": '{"customer":123}',
            "_save": "Save",
        },
    )
    assert response.status_code == 200
    assert set(response.context["adminform"].form.errors) == {"snapshot"}
    order.refresh_from_db()
    assert (order.status, order.snapshot.customer) == ("new", "Alice")
