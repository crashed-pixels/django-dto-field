import pytest
from dict_field.adapters import MappingAdapter, Message, MessageAdapter, MessageSchema
from django.core.exceptions import ValidationError
from django.db.migrations.writer import MigrationWriter

from django_dto_field.adapters.msgspec import MsgspecAdapter
from django_dto_field.conversion.converter import DTOConverter
from django_dto_field.exceptions.base import DTOValidationError, SchemaError
from django_dto_field.exceptions.django import DTOFieldError
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.char import DTOCharField
from django_dto_field.fields.json import DTOJSONField


def test_explicit_adapter_decouples_schema_from_dto_type():
    converter = DTOConverter(MessageSchema, adapter=MessageAdapter)
    message = Message(7)
    assert converter.is_instance(message)
    assert not converter.is_instance(MessageSchema())
    assert not converter.is_instance({"identifier": 7})
    assert converter.to_data(message) == {"identifier": 7}
    assert converter.from_data({"identifier": 7}) == message


def test_adapters_are_selected_per_converter_without_registration():
    class StrictSchema(MessageSchema):
        minimum = 10

    normal = DTOConverter(MessageSchema, adapter=MessageAdapter)
    strict = DTOConverter(StrictSchema, adapter=MessageAdapter)
    assert normal.from_data({"identifier": 1}) == Message(1)
    with pytest.raises(DTOValidationError):
        strict.from_data({"identifier": 1})
    # Using an adapter must not change default schema selection anywhere else.
    with pytest.raises(SchemaError):
        DTOConverter(MessageSchema)


def test_custom_adapter_dump_is_validated_even_for_mutated_instances():
    converter = DTOConverter(MessageSchema, adapter=MessageAdapter)
    message = Message(1)
    message.identifier = -1
    with pytest.raises(DTOValidationError) as error:
        converter.to_data(message)
    assert isinstance(error.value.__cause__, ValueError)


def test_converter_checks_common_shape_and_instance_requirements():
    converter = DTOConverter(MessageSchema, adapter=MessageAdapter)
    with pytest.raises(DTOValidationError):
        converter.from_data([1])
    with pytest.raises(DTOValidationError):
        converter.to_data(object())


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField, DTOJSONField])
def test_custom_adapter_survives_migration_serialization(field_class):
    field = field_class(schema=MessageSchema, adapter=MessageAdapter, max_length=100)
    source, imports = MigrationWriter.serialize(field)
    namespace = {}
    exec("\n".join(sorted(imports)), namespace)
    restored = eval(source, namespace)
    assert restored.schema is MessageSchema
    assert restored.deconstruct()[3]["adapter"] is MessageAdapter
    assert restored.to_python({"identifier": 1}) == Message(1)
    message = Message(2)
    assert restored.to_python(message) is message


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField, DTOJSONField])
def test_default_adapter_is_omitted_from_migrations(field_class):
    assert "adapter" not in field_class().deconstruct()[3]


@pytest.mark.parametrize("field_class", [DTOCharField, DTOBinaryField, DTOJSONField])
def test_custom_adapter_errors_use_the_django_boundary(field_class):
    field = field_class(schema=MessageSchema, adapter=MessageAdapter)
    with pytest.raises(DTOFieldError) as error:
        field.to_python({"identifier": -1})
    assert isinstance(error.value, ValidationError)
    assert isinstance(error.value.__cause__, DTOValidationError)
    with pytest.raises(DTOFieldError) as invalid_schema:
        field_class(schema=dict, adapter=MessageAdapter)
    assert isinstance(invalid_schema.value.__cause__, SchemaError)


def test_mapping_result_adapter_preserves_partial_json_lookup_operands():
    field = DTOJSONField(schema=MessageSchema, adapter=MappingAdapter)
    assert field.to_python({"identifier": 1}) == {"identifier": 1}
    partial = {"another_key": "lookup operand"}
    assert field.get_prep_value(partial) is partial
    assert field.get_prep_value(7) == 7
    with pytest.raises(DTOFieldError):
        field.to_python(partial)


def test_builtin_adapter_can_be_selected_explicitly():
    field = DTOJSONField(adapter=MsgspecAdapter)
    assert field.to_python({"a": 1}) == {"a": 1}
    assert field.deconstruct()[3]["adapter"] is MsgspecAdapter
