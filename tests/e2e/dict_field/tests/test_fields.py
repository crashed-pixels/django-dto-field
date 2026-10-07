import json

import pytest
from django import forms
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import connection, models

from dict_field.adapters import Message
from dict_field.models import (
    Address,
    CustomModel,
    DataclassModel,
    DictModel,
    NullableModel,
    UserDTO,
)

pytestmark = pytest.mark.django_db
FIELD_NAMES = ("text", "binary", "json")
DTO_CASES = (
    (DictModel, {"nested": [1, None, True, "Привет"]}),
    (DataclassModel, UserDTO(1, Address("London"))),
    (CustomModel, Message(1)),
)


@pytest.mark.parametrize("model, payload", DTO_CASES)
def test_create_read_and_full_clean(model, payload):
    instance = model(**dict.fromkeys(FIELD_NAMES, payload))
    instance.full_clean()
    instance.save()
    instance.refresh_from_db()
    for field_name in FIELD_NAMES:
        assert getattr(instance, field_name) == payload
        assert (
            model.objects.values_list(field_name, flat=True).get(pk=instance.pk)
            == payload
        )
        assert (
            getattr(model.objects.defer(field_name).get(pk=instance.pk), field_name)
            == payload
        )


@pytest.mark.parametrize("model, payload", DTO_CASES)
@pytest.mark.parametrize("field_name", FIELD_NAMES)
def test_orm_filters_accept_dto_values(model, payload, field_name):
    instance = model.objects.create(**dict.fromkeys(FIELD_NAMES, payload))
    assert model.objects.filter(**{field_name: payload}).get() == instance
    assert model.objects.filter(**{f"{field_name}__in": [payload]}).get() == instance


def test_native_database_representations():
    instance = DictModel.objects.create(**dict.fromkeys(FIELD_NAMES, {"a": 1}))
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT "text", "binary", "json" FROM "dict_field_dictmodel" WHERE id = %s',
            [instance.pk],
        )
        text, binary, json_value = cursor.fetchone()
    assert text == '{"a":1}'
    assert bytes(binary) == b'{"a":1}'
    assert json.loads(json_value) == {"a": 1}


@pytest.mark.parametrize(
    "model, payload, changed",
    [
        (DictModel, {"a": 1}, {"a": 2}),
        (DataclassModel, UserDTO(1, Address("London")), UserDTO(2, Address("Paris"))),
        (CustomModel, Message(1), Message(2)),
    ],
)
def test_bulk_and_expression_writes(model, payload, changed):
    instances = model.objects.bulk_create(
        [model(**dict.fromkeys(FIELD_NAMES, payload)) for _ in range(2)]
    )
    for instance in instances:
        for field_name in FIELD_NAMES:
            setattr(instance, field_name, changed)
    model.objects.bulk_update(instances, FIELD_NAMES)
    for field_name in FIELD_NAMES:
        assert list(model.objects.values_list(field_name, flat=True)) == [
            changed,
            changed,
        ]
        model.objects.update(**{field_name: payload})
        model.objects.update(**{field_name: models.F(field_name)})
        assert list(model.objects.values_list(field_name, flat=True)) == [
            payload,
            payload,
        ]
        model.objects.update(
            **{
                field_name: models.Value(
                    changed, output_field=model._meta.get_field(field_name)
                )
            }
        )
        assert list(model.objects.values_list(field_name, flat=True)) == [
            changed,
            changed,
        ]


def test_nulls_defaults_and_mutation():
    nullable = NullableModel.objects.create()
    nullable.refresh_from_db()
    nullable.full_clean()
    for field_name in FIELD_NAMES:
        assert getattr(nullable, field_name) is None
        assert NullableModel.objects.filter(**{f"{field_name}__isnull": True}).exists()
    first, second = DictModel.objects.create(), DictModel.objects.create()
    first.text["changed"] = True
    first.save(update_fields=["text"])
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.text == {"changed": True}
    assert second.text == first.binary == first.json == {}


@pytest.mark.parametrize("field_name", FIELD_NAMES)
def test_invalid_writes_raise_django_validation_error(field_name):
    instance = DataclassModel.objects.create(
        **dict.fromkeys(FIELD_NAMES, UserDTO(1, Address("London")))
    )
    setattr(instance, field_name, UserDTO("bad", Address("London")))
    with pytest.raises(ValidationError):
        instance.save()
    with pytest.raises(ValidationError):
        DataclassModel.objects.filter(pk=instance.pk).update(
            **{field_name: {"identifier": "bad"}}
        )


def test_json_key_lookups_return_native_values():
    instance = DictModel.objects.create(
        json={
            "number": 1,
            "name": "Ada",
            "nested": {"ok": True},
            "list": [1, 2],
            "null": None,
        }
    )
    assert (
        DictModel.objects.filter(
            json__number=1, json__name="Ada", json__nested__ok=True
        ).get()
        == instance
    )
    assert DictModel.objects.filter(json__number__in=[1, 2]).exists()
    assert DictModel.objects.filter(json__has_key="name").exists()
    for key, expected in instance.json.items():
        assert (
            DictModel.objects.values_list(f"json__{key}", flat=True).get() == expected
        )
    user = DataclassModel.objects.create(
        **dict.fromkeys(FIELD_NAMES, UserDTO(1, Address("London")))
    )
    assert DataclassModel.objects.filter(json__address__city="London").get() == user
    assert DataclassModel.objects.values_list("json__address", flat=True).get() == {
        "city": "London"
    }


@pytest.mark.parametrize(
    "model, payload",
    [
        (DictModel, {"a": [1, None]}),
        (DataclassModel, UserDTO(1, Address("London"))),
        (NullableModel, None),
        (CustomModel, Message(1)),
    ],
)
def test_django_fixture_round_trip(model, payload):
    instance = model.objects.create(**dict.fromkeys(FIELD_NAMES, payload))
    fixture = serializers.serialize("json", [instance])
    restored = next(serializers.deserialize("json", fixture)).object
    for field_name in FIELD_NAMES:
        assert getattr(restored, field_name) == payload
    restored.save()


@pytest.mark.parametrize(
    "field_name, malformed",
    [("text", "not json"), ("binary", b"not json"), ("json", '{"identifier":"bad"}')],
)
def test_corrupted_database_values_raise_validation_error(field_name, malformed):
    instance = DataclassModel.objects.create(
        **dict.fromkeys(FIELD_NAMES, UserDTO(1, Address("London")))
    )
    with connection.cursor() as cursor:
        column = connection.ops.quote_name(field_name)
        cursor.execute(
            f"UPDATE dict_field_dataclassmodel SET {column} = %s WHERE id = %s",
            [malformed, instance.pk],
        )
    with pytest.raises(ValidationError):
        instance.refresh_from_db()


def test_model_form_converts_json_to_nested_dataclass():
    form_class = forms.modelform_factory(DataclassModel, fields=["text", "json"])
    payload = '{"identifier":1,"address":{"city":"London"}}'
    form = form_class(data={"text": payload, "json": payload})
    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    instance.binary = instance.json
    instance.save()
    instance.refresh_from_db()
    assert instance.json == UserDTO(1, Address("London"))
    assert instance.text == instance.json
    initial = form_class(instance=instance)
    assert json.loads(initial["text"].value()) == json.loads(payload)
    assert json.loads(initial["json"].value()) == json.loads(payload)
    assert not form_class(
        instance=instance, data={"text": payload, "json": payload}
    ).has_changed()


def test_invalid_model_form_reports_errors():
    form_class = forms.modelform_factory(DataclassModel, fields=["text", "json"])
    form = form_class(data={"text": "not json", "json": '{"identifier":"bad"}'})
    assert not form.is_valid()
    assert set(form.errors) == {"text", "json"}


def test_json_null_expression_retains_native_json_semantics():
    field = NullableModel._meta.get_field("json")
    instance = NullableModel.objects.create(json=models.Value(None, output_field=field))
    instance.refresh_from_db()
    assert instance.json is None
    assert NullableModel.objects.filter(json=None).exists()
    assert not NullableModel.objects.filter(json__isnull=True).exists()


def test_dataclass_json_expression_annotation():
    DictModel.objects.create()
    schema_field = DataclassModel._meta.get_field("json")
    user = UserDTO(2, Address("Paris"))
    assert (
        DictModel.objects.annotate(dto=models.Value(user, output_field=schema_field))
        .values_list("dto", flat=True)
        .get()
        == user
    )


def test_custom_adapter_model_forms_and_json_key_lookups():
    instance = CustomModel.objects.create(**dict.fromkeys(FIELD_NAMES, Message(7)))
    assert CustomModel.objects.filter(json__identifier=7).get() == instance
    assert CustomModel.objects.values_list("json__identifier", flat=True).get() == 7
    form_class = forms.modelform_factory(CustomModel, fields=["text", "json"])
    initial = form_class(instance=instance)
    assert json.loads(initial["text"].value()) == {"identifier": 7}
    assert json.loads(initial["json"].value()) == {"identifier": 7}
    payload = dict.fromkeys(["text", "json"], '{"identifier":7}')
    unchanged = form_class(instance=instance, data=payload)
    assert not unchanged.has_changed()
    assert unchanged.is_valid(), unchanged.errors
    changed = form_class(
        instance=instance, data=dict.fromkeys(payload, '{"identifier":8}')
    )
    assert changed.has_changed()
    assert changed.is_valid(), changed.errors
    changed.save()
    instance.refresh_from_db()
    assert instance.text == instance.json == Message(8)


@pytest.mark.parametrize("field_name", FIELD_NAMES)
def test_custom_adapter_rejects_invalid_orm_writes(field_name):
    instance = CustomModel.objects.create(**dict.fromkeys(FIELD_NAMES, Message(7)))
    with pytest.raises(ValidationError):
        CustomModel.objects.filter(pk=instance.pk).update(**{field_name: Message(-1)})
