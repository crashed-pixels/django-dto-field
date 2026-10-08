"""Exercise customer edits, partial saves, defaults, and ORM shortcuts."""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from dict_field.adapters import Message
from dict_field.models import (
    Address,
    CustomModel,
    DataclassModel,
    DictModel,
    MappingModel,
    Order,
    UserDTO,
)

pytestmark = pytest.mark.django_db
ORDER_FIELDS = ("snapshot", "text", "binary")


@pytest.mark.parametrize("field_name", ORDER_FIELDS)
def test_nested_edit_survives_save_and_reload(order, field_name):
    snapshot = getattr(order, field_name)
    snapshot.tags.append("gift")
    snapshot.note = "Leave at reception"
    order.save(update_fields=[field_name])
    order.refresh_from_db()
    assert getattr(order, field_name).tags == ["gift"]
    assert getattr(order, field_name).note == "Leave at reception"


@pytest.mark.parametrize("field_name", ORDER_FIELDS)
def test_invalid_mutation_leaves_stored_snapshot_unchanged(order, field_name):
    getattr(order, field_name).customer = 123
    with pytest.raises(ValidationError), transaction.atomic():
        order.save(update_fields=[field_name])
    order.refresh_from_db()
    assert getattr(order, field_name).customer == "Alice"


@pytest.mark.parametrize("field_name", ("text", "binary", "json"))
@pytest.mark.parametrize("model", (CustomModel, MappingModel))
def test_adapter_mutations_are_revalidated_on_save(model, field_name):
    payload = Message(1) if model is CustomModel else {"identifier": 1}
    instance = model.objects.create(
        **dict.fromkeys(("text", "binary", "json"), payload)
    )
    instance.refresh_from_db()
    assigned = getattr(instance, field_name)
    if model is CustomModel:
        assigned.identifier = -1
    else:
        assigned["identifier"] = -1
    with pytest.raises(ValidationError), transaction.atomic():
        instance.save(update_fields=[field_name])
    instance.refresh_from_db()
    expected = Message(1) if model is CustomModel else {"identifier": 1}
    assert getattr(instance, field_name) == expected


def test_partial_save_does_not_write_other_modified_fields(order):
    order.status = "paid"
    order.snapshot.note = "unsaved"
    order.save(update_fields=["status"])
    order.refresh_from_db()
    assert (order.status, order.snapshot.note) == ("paid", None)


def test_partial_save_ignores_invalid_excluded_dto(order):
    order.snapshot.customer = 123
    order.status = "paid"
    order.save(update_fields=["status"])
    order.refresh_from_db()
    assert (order.status, order.snapshot.customer) == ("paid", "Alice")


def test_only_loads_snapshot_once(order, django_assert_num_queries):
    deferred = Order.objects.only("id", "status").get(pk=order.pk)
    with django_assert_num_queries(1):
        assert deferred.snapshot.customer == "Alice"
    with django_assert_num_queries(0):
        assert deferred.snapshot.customer == "Alice"


def test_assignment_to_deferred_snapshot_does_not_fetch_old_value(
    order, snapshot, django_assert_num_queries
):
    deferred = Order.objects.defer("snapshot").get(pk=order.pk)
    snapshot.note = "replacement"
    with django_assert_num_queries(0):
        deferred.snapshot = snapshot
    deferred.save(update_fields=["snapshot"])
    order.refresh_from_db()
    assert order.snapshot.note == "replacement"


def test_saving_deferred_order_does_not_overwrite_snapshot(order):
    deferred = Order.objects.only("id", "status").get(pk=order.pk)
    Order.objects.filter(pk=order.pk).update(
        snapshot={
            **Order._meta.get_field("snapshot").converter.to_data(order.snapshot),
            "note": "updated elsewhere",
        }
    )
    deferred.status = "paid"
    deferred.save()
    order.refresh_from_db()
    assert (order.status, order.snapshot.note) == ("paid", "updated elsewhere")


def test_selective_refresh_preserves_unsaved_other_fields(order):
    Order.objects.filter(pk=order.pk).update(status="paid")
    order.snapshot.note = "local edit"
    order.refresh_from_db(fields=["status"])
    assert (order.status, order.snapshot.note) == ("paid", "local edit")


@pytest.mark.parametrize("method", ("get_or_create", "update_or_create"))
def test_orm_shortcuts_create_from_callable_defaults(method):
    instance, created = getattr(DataclassModel.objects, method)(
        pk=101,
        defaults=dict.fromkeys(
            ("text", "binary", "json"),
            lambda: {"identifier": 1, "address": {"city": "Paris"}},
        ),
    )
    instance.refresh_from_db()
    assert created
    assert (
        instance.text
        == instance.binary
        == instance.json
        == UserDTO(1, Address("Paris"))
    )


def test_get_or_create_does_not_evaluate_defaults_for_existing_row(order):
    def invalid_default():
        raise AssertionError("Existing rows must not evaluate create defaults")

    found, created = Order.objects.get_or_create(
        pk=order.pk, defaults={"snapshot": invalid_default}
    )
    assert not created
    assert found.snapshot == order.snapshot


def test_update_or_create_edits_existing_snapshot(order, snapshot):
    snapshot.note = "updated"
    _, created = Order.objects.update_or_create(
        pk=order.pk, defaults={"snapshot": snapshot, "status": "paid"}
    )
    order.refresh_from_db()
    assert not created
    assert (order.status, order.snapshot.note) == ("paid", "updated")


@pytest.mark.parametrize("method", ("get_or_create", "update_or_create"))
def test_orm_shortcuts_reject_invalid_create_values(method):
    with pytest.raises(ValidationError):
        getattr(DataclassModel.objects, method)(
            pk=101, defaults={"json": {"identifier": "bad"}}
        )
    assert not DataclassModel.objects.exists()


def test_invalid_update_or_create_preserves_existing_row(order):
    with pytest.raises(ValidationError):
        Order.objects.update_or_create(
            pk=order.pk, defaults={"snapshot": {"customer": 123}}
        )
    order.refresh_from_db()
    assert order.snapshot.customer == "Alice"


def test_callable_defaults_are_independent_between_fields_and_instances(order):
    second = Order.objects.create(customer=order.customer)
    order.snapshot.tags.append("gift")
    assert second.snapshot.tags == order.text.tags == order.binary.tags == []


def test_dictionary_defaults_are_independent():
    first, second = DictModel(), DictModel()
    first.json["new"] = True
    assert second.json == first.text == first.binary == {}


def test_mapping_adapter_round_trip_lookups_and_partial_operands():
    instance = MappingModel.objects.create(
        text={"identifier": 7}, binary={"identifier": 7}, json={"identifier": 7}
    )
    instance.refresh_from_db()
    assert instance.text == instance.binary == instance.json == {"identifier": 7}
    assert MappingModel.objects.filter(json__identifier=7).get() == instance
    assert MappingModel.objects.values_list("json__identifier", flat=True).get() == 7
    assert not MappingModel.objects.filter(json={"unrelated": "operand"}).exists()
    with pytest.raises(ValidationError):
        MappingModel.objects.filter(pk=instance.pk).update(json={"unrelated": "write"})
