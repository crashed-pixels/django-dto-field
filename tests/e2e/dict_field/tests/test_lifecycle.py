"""Exercise fixture commands, historical models, and schema evolution."""

import json
from io import StringIO

import pytest
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.serializers.base import DeserializationError
from django.db.migrations.state import ModelState, ProjectState
from django.db.migrations.writer import MigrationWriter

from dict_field.adapters import MappingAdapter, MessageSchema
from dict_field.models import (
    Address,
    DataclassModel,
    DictModel,
    MappingModel,
    OptOutModel,
    Order,
    UserDTO,
)
from dict_field.schemas import NumericPreferences, Preferences, RequiredPreferences

pytestmark = pytest.mark.django_db


def test_rich_fixture_restores_deleted_order(order):
    primary_key = order.pk
    expected = order.snapshot
    fixture = serializers.serialize("json", [order])
    order.delete()
    for restored in serializers.deserialize("json", fixture):
        restored.save()
    loaded = Order.objects.get(pk=primary_key)
    assert loaded.snapshot == loaded.text == loaded.binary == expected


@pytest.mark.parametrize("model", (DictModel, DataclassModel, MappingModel))
def test_dumpdata_loaddata_restores_deleted_rows(model, tmp_path):
    if model is DataclassModel:
        payload = UserDTO(1, Address("London"))
    elif model is MappingModel:
        payload = {"identifier": 7}
    else:
        payload = {"tags": ["Привет", None]}
    instance = model.objects.create(
        **dict.fromkeys(("text", "binary", "json"), payload)
    )
    primary_key = instance.pk
    output = StringIO()
    call_command("dumpdata", model._meta.label, stdout=output)
    fixture = tmp_path / "records.json"
    fixture.write_text(output.getvalue(), encoding="utf-8")
    instance.delete()
    call_command("loaddata", str(fixture), verbosity=0)
    restored = model.objects.get(pk=primary_key)
    assert restored.text == restored.binary == restored.json == payload


def test_invalid_fixture_rolls_back_preceding_valid_record(tmp_path):
    payload = UserDTO(1, Address("London"))
    instances = [
        DataclassModel.objects.create(
            **dict.fromkeys(("text", "binary", "json"), payload)
        )
        for _ in range(2)
    ]
    records = json.loads(serializers.serialize("json", instances))
    records[1]["fields"]["json"]["identifier"] = "bad"
    DataclassModel.objects.all().delete()
    fixture = tmp_path / "invalid.json"
    fixture.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(DeserializationError):
        call_command("loaddata", str(fixture), verbosity=0)
    assert not DataclassModel.objects.exists()


@pytest.mark.parametrize("model", (MappingModel, OptOutModel))
def test_migration_serialization_renders_historical_field_behavior(model):
    state = ProjectState()
    model_state = ModelState.from_model(model)
    for name in ("text", "binary", "json"):
        source, imports = MigrationWriter.serialize(model_state.fields[name])
        namespace = {}
        exec("\n".join(sorted(imports)), namespace)
        model_state.fields[name] = eval(source, namespace)
    state.add_model(model_state)
    historical = state.apps.get_model("dict_field", model.__name__)
    field = historical._meta.get_field("json")
    if model is MappingModel:
        assert field.schema is MessageSchema
        assert field.adapter is MappingAdapter
        instance = historical.objects.create(
            text={"identifier": 1}, binary={"identifier": 1}, json={"identifier": 1}
        )
        with pytest.raises(ValidationError):
            instance.json = {"identifier": -1}
        instance.refresh_from_db()
        assert instance.json == {"identifier": 1}
    else:
        assert field.validate_on_assignment is False
        instance = historical(json={"identifier": "bad"})
        assert instance.json == {"identifier": "bad"}
        with pytest.raises(ValidationError):
            field.to_python(instance.json)


@pytest.mark.parametrize("field_name", ("text", "binary", "json"))
def test_old_payload_loads_new_member_default(field_name):
    original = DictModel.objects.create(**{field_name: {"theme": "dark"}})
    state = ProjectState()
    model_state = ModelState.from_model(DictModel)
    field_class = type(model_state.fields[field_name])
    model_state.fields[field_name] = field_class(schema=Preferences, max_length=1000)
    state.add_model(model_state)
    historical = state.apps.get_model("dict_field", "DictModel")
    instance = historical.objects.get(pk=original.pk)
    assert getattr(instance, field_name) == Preferences("dark", notifications=True)
    getattr(instance, field_name).notifications = False
    instance.save(update_fields=[field_name])
    original.refresh_from_db()
    assert getattr(original, field_name) == {"theme": "dark", "notifications": False}


@pytest.mark.parametrize("schema", (RequiredPreferences, NumericPreferences))
@pytest.mark.parametrize("field_name", ("text", "binary", "json"))
def test_incompatible_schema_change_rejects_existing_payload(schema, field_name):
    original = DictModel.objects.create(**{field_name: {"theme": "dark"}})
    state = ProjectState()
    model_state = ModelState.from_model(DictModel)
    field_class = type(model_state.fields[field_name])
    model_state.fields[field_name] = field_class(schema=schema, max_length=1000)
    state.add_model(model_state)
    historical = state.apps.get_model("dict_field", "DictModel")
    with pytest.raises(ValidationError):
        historical.objects.get(pk=original.pk)
    original.refresh_from_db()
    assert getattr(original, field_name) == {"theme": "dark"}
