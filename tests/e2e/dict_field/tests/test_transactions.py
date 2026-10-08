"""Exercise batch imports and atomic order/audit writes."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, transaction

from dict_field.models import Address, AuditEvent, DataclassModel, Order, UserDTO

pytestmark = pytest.mark.django_db(transaction=True)
FIELDS = ("text", "binary", "json")


def test_bulk_import_reconstructs_dictionary_inputs():
    payload = {"identifier": 1, "address": {"city": "London"}}
    DataclassModel.objects.bulk_create(
        [DataclassModel(**dict.fromkeys(FIELDS, payload)) for _ in range(3)],
        batch_size=1,
    )
    assert (
        list(DataclassModel.objects.values_list("json", flat=True))
        == [UserDTO(1, Address("London"))] * 3
    )


@pytest.mark.parametrize("field_name", FIELDS)
def test_bulk_update_persists_nested_mutations(field_name):
    DataclassModel.objects.bulk_create(
        [
            DataclassModel(**dict.fromkeys(FIELDS, UserDTO(1, Address("London"))))
            for _ in range(2)
        ]
    )
    instances = list(DataclassModel.objects.order_by("pk"))
    for instance in instances:
        getattr(instance, field_name).address.city = "Paris"
    DataclassModel.objects.bulk_update(instances, [field_name], batch_size=1)
    assert (
        list(DataclassModel.objects.values_list(field_name, flat=True))
        == [UserDTO(1, Address("Paris"))] * 2
    )


@pytest.mark.parametrize("field_name", FIELDS)
def test_invalid_later_batch_rolls_back_bulk_update(field_name):
    DataclassModel.objects.bulk_create(
        [
            DataclassModel(**dict.fromkeys(FIELDS, UserDTO(1, Address("London"))))
            for _ in range(2)
        ]
    )
    instances = list(DataclassModel.objects.order_by("pk"))
    getattr(instances[0], field_name).address.city = "Paris"
    getattr(instances[1], field_name).identifier = "bad"
    with pytest.raises(ValidationError), transaction.atomic():
        DataclassModel.objects.bulk_update(instances, [field_name], batch_size=1)
    assert (
        list(DataclassModel.objects.values_list(field_name, flat=True))
        == [UserDTO(1, Address("London"))] * 2
    )


def test_invalid_later_import_batch_rolls_back_prior_insert():
    valid = DataclassModel(**dict.fromkeys(FIELDS, UserDTO(1, Address("London"))))
    invalid = DataclassModel(**dict.fromkeys(FIELDS, UserDTO(2, Address("Paris"))))
    invalid.json.identifier = "bad"
    with pytest.raises(ValidationError), transaction.atomic():
        DataclassModel.objects.bulk_create([valid], batch_size=1)
        DataclassModel.objects.bulk_create([invalid], batch_size=1)
    assert not DataclassModel.objects.exists()


def test_order_and_audit_write_roll_back_together(order):
    with pytest.raises(ValidationError), transaction.atomic():
        order.status = "paid"
        order.save(update_fields=["status"])
        AuditEvent.objects.create(details={"order": order.pk})
        order.snapshot.customer = 123
        order.save(update_fields=["snapshot"])
    order.refresh_from_db()
    assert order.status == "new"
    assert not AuditEvent.objects.exists()


def test_nested_savepoint_keeps_valid_outer_work(order):
    with transaction.atomic():
        order.status = "paid"
        order.save(update_fields=["status"])
        with pytest.raises(ValidationError), transaction.atomic():
            AuditEvent.objects.create(details={"order": order.pk})
            order.snapshot.customer = 123
            order.save(update_fields=["snapshot"])
    order.refresh_from_db()
    assert order.status == "paid"
    assert not AuditEvent.objects.exists()


def test_bulk_upsert_replaces_snapshot(order, snapshot):
    if not connection.features.supports_update_conflicts:
        pytest.skip("Backend does not support bulk upserts")
    snapshot.note = "replacement"
    options = (
        {"unique_fields": ["pk"]}
        if connection.features.supports_update_conflicts_with_target
        else {}
    )
    Order.objects.bulk_create(
        [Order(pk=order.pk, customer=order.customer, snapshot=snapshot)],
        update_conflicts=True,
        update_fields=["snapshot"],
        **options,
    )
    order.refresh_from_db()
    assert order.snapshot.note == "replacement"
