"""Exercise create/edit forms, optional inputs, validators, and formsets."""

import json

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from dict_field.forms import OrderForm
from dict_field.models import (
    LengthModel,
    MappingModel,
    OptionalSettings,
    Order,
    ValidatedModel,
)

pytestmark = pytest.mark.django_db


def test_create_form_saves_rich_snapshot_directly(order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    form = OrderForm(
        data={
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
        }
    )
    assert form.is_valid(), form.errors
    created = form.save()
    created.refresh_from_db()
    assert created.snapshot == order.snapshot


def test_edit_form_reconstructs_nested_line_items(order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    payload["items"].append({"sku": "gift", "quantity": 1})
    form = OrderForm(
        instance=order,
        data={
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
        },
    )
    assert form.is_valid(), form.errors
    form.save()
    order.refresh_from_db()
    assert order.snapshot.items[-1].sku == "gift"


def test_invalid_form_keeps_stored_order_unchanged(order):
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    payload["items"][0]["quantity"] = "many"
    form = OrderForm(
        instance=order,
        data={
            "customer": order.customer_id,
            "status": "paid",
            "snapshot": json.dumps(payload),
        },
    )
    assert not form.is_valid()
    assert set(form.errors) == {"snapshot"}
    order.refresh_from_db()
    assert (order.status, order.snapshot.items[0].quantity) == ("new", 2)


@pytest.mark.parametrize("value", ("", "null"))
def test_required_dict_form_rejects_empty_and_null(value):
    form_class = forms.modelform_factory(OptionalSettings, fields=["required"])
    form = form_class(data={"required": value})
    assert not form.is_valid()
    assert "required" in form.errors


def test_required_dict_form_rejects_empty_object():
    form_class = forms.modelform_factory(OptionalSettings, fields=["required"])
    assert not form_class(data={"required": "{}"}).is_valid()


def test_blank_dict_form_accepts_empty_object():
    form_class = forms.modelform_factory(
        OptionalSettings, fields=["required", "optional"]
    )
    form = form_class(data={"required": '{"active":true}', "optional": "{}"})
    assert form.is_valid(), form.errors
    instance = form.save()
    instance.refresh_from_db()
    assert instance.optional == {}


@pytest.mark.parametrize("value", ("", "null"))
def test_nullable_form_persists_sql_null(value):
    form_class = forms.modelform_factory(
        OptionalSettings, fields=["required", "nullable"]
    )
    form = form_class(data={"required": '{"active":true}', "nullable": value})
    assert form.is_valid(), form.errors
    instance = form.save()
    assert OptionalSettings.objects.filter(
        pk=instance.pk, nullable__isnull=True
    ).exists()


def test_omitted_optional_input_retains_callable_default():
    form_class = forms.modelform_factory(
        OptionalSettings, fields=["required", "optional"]
    )
    form = form_class(data={"required": '{"active":true}'})
    assert form.is_valid(), form.errors
    instance = form.save()
    instance.refresh_from_db()
    assert instance.optional == {}


def test_blank_does_not_allow_sql_null_in_nonnullable_field():
    form_class = forms.modelform_factory(
        OptionalSettings, fields=["required", "optional"]
    )
    form = form_class(data={"required": '{"active":true}', "optional": ""})
    assert form.is_valid(), form.errors
    with pytest.raises(IntegrityError), transaction.atomic():
        form.save()
    assert not OptionalSettings.objects.exists()


@pytest.mark.parametrize("field_name", ("binary", "json"))
def test_full_clean_validators_receive_storage_values(field_name):
    instance = ValidatedModel(binary={"allowed": True}, json={"allowed": True})
    instance.full_clean()
    setattr(instance, field_name, {"allowed": False})
    with pytest.raises(ValidationError) as error:
        instance.full_clean()
    assert field_name in error.value.message_dict


def test_model_form_reports_storage_validator_errors():
    form_class = forms.modelform_factory(ValidatedModel, fields=["json"])
    form = form_class(data={"json": '{"allowed":false}'})
    assert not form.is_valid()
    assert set(form.errors) == {"json"}


def test_serialized_length_exact_boundary_is_valid():
    form_class = forms.modelform_factory(LengthModel, fields=["binary"])
    form = form_class(data={"binary": '{"x":"ab"}'})
    assert form.is_valid(), form.errors


def test_unicode_length_counts_binary_bytes():
    instance = LengthModel(binary={"x": "éé"})
    with pytest.raises(ValidationError) as error:
        instance.full_clean()
    assert set(error.value.message_dict) == {"binary"}


def test_model_form_rejects_serialized_length_overflow():
    form_class = forms.modelform_factory(LengthModel, fields=["binary"])
    form = form_class(data={"binary": '{"x":"abc"}'})
    assert not form.is_valid()
    assert "binary" in form.errors


def test_mapping_result_adapter_model_form_round_trip():
    form_class = forms.modelform_factory(MappingModel, fields=["json"])
    instance = MappingModel.objects.create(
        binary={"identifier": 1}, json={"identifier": 1}
    )
    form = form_class(instance=instance, data={"json": '{"identifier":2}'})
    assert form.is_valid(), form.errors
    form.save()
    instance.refresh_from_db()
    assert instance.json == {"identifier": 2}


@pytest.mark.parametrize("invalid", (False, True))
def test_formset_saves_only_when_all_snapshots_are_valid(order, invalid):
    second = Order.objects.create(customer=order.customer)
    formset_class = forms.modelformset_factory(Order, fields=["snapshot"], extra=0)
    payload = Order._meta.get_field("snapshot").converter.to_data(order.snapshot)
    changed = {**payload, "note": "gift"}
    second_payload = {**changed, "customer": 123} if invalid else changed
    formset = formset_class(
        data={
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-0-id": order.pk,
            "form-0-snapshot": json.dumps(changed),
            "form-1-id": second.pk,
            "form-1-snapshot": json.dumps(second_payload),
        },
        queryset=Order.objects.order_by("pk"),
    )
    if formset.is_valid():
        formset.save()
    assert formset.is_valid() is not invalid
    assert list(
        Order.objects.order_by("pk").values_list("snapshot__note", flat=True)
    ) == ([None, None] if invalid else ["gift", "gift"])
