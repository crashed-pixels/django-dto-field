"""Exercise order forms through actual HTTP requests."""

import json

import pytest
from django.urls import reverse

from dict_field.models import Order

pytestmark = pytest.mark.django_db


def test_http_create_persists_rich_snapshot(client, order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    response = client.post(
        reverse("order-create"),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
        },
    )
    created = Order.objects.exclude(pk=order.pk).get()
    assert response.status_code == 302
    assert response.url == reverse("order-edit", args=[created.pk])
    assert created.snapshot == order.snapshot


def test_http_get_renders_dto_as_json(client, order):
    response = client.get(reverse("order-edit", args=[order.pk]))
    assert response.status_code == 200
    assert b"Alice" in response.content
    assert b"book" in response.content


def test_invalid_http_edit_reports_error_without_saving(client, order):
    response = client.post(
        reverse("order-edit", args=[order.pk]),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": '{"customer":123}',
        },
    )
    assert response.status_code == 400
    assert b"errorlist" in response.content
    order.refresh_from_db()
    assert (order.status, order.snapshot.customer) == ("new", "Alice")


def test_valid_http_edit_persists_snapshot(client, order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    payload["note"] = "HTTP edit"
    response = client.post(
        reverse("order-edit", args=[order.pk]),
        {
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
        },
    )
    assert response.status_code == 302
    order.refresh_from_db()
    assert (order.status, order.snapshot.note) == ("paid", "HTTP edit")
