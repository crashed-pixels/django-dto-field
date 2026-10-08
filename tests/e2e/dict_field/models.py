from dataclasses import dataclass

from django.db import models

from dict_field.adapters import MappingAdapter, MessageAdapter, MessageSchema
from dict_field.schemas import OrderSnapshot, default_snapshot
from dict_field.validators import binary_validator, mapping_validator, text_validator
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.char import DTOCharField
from django_dto_field.fields.json import DTOJSONField


@dataclass
class Address:
    city: str


@dataclass
class UserDTO:
    identifier: int
    address: Address


class DictModel(models.Model):
    text = DTOCharField(max_length=1000, default=dict, blank=True)
    binary = DTOBinaryField(default=dict, blank=True)
    json = DTOJSONField(default=dict, blank=True)


class DataclassModel(models.Model):
    text = DTOCharField(schema=UserDTO, max_length=1000)
    binary = DTOBinaryField(schema=UserDTO)
    json = DTOJSONField(schema=UserDTO)


class OptOutModel(models.Model):
    text = DTOCharField(schema=UserDTO, max_length=1000, validate_on_assignment=False)
    binary = DTOBinaryField(schema=UserDTO, validate_on_assignment=False)
    json = DTOJSONField(schema=UserDTO, validate_on_assignment=False)


class NullableModel(models.Model):
    text = DTOCharField(schema=UserDTO, max_length=1000, null=True, blank=True)
    binary = DTOBinaryField(schema=UserDTO, null=True, blank=True)
    json = DTOJSONField(schema=UserDTO, null=True, blank=True)


class CustomModel(models.Model):
    text = DTOCharField(schema=MessageSchema, adapter=MessageAdapter, max_length=1000)
    binary = DTOBinaryField(schema=MessageSchema, adapter=MessageAdapter)
    json = DTOJSONField(schema=MessageSchema, adapter=MessageAdapter)


class MappingModel(models.Model):
    text = DTOCharField(schema=MessageSchema, adapter=MappingAdapter, max_length=1000)
    binary = DTOBinaryField(schema=MessageSchema, adapter=MappingAdapter)
    json = DTOJSONField(schema=MessageSchema, adapter=MappingAdapter)


class Customer(models.Model):
    name = models.CharField(max_length=100)


class SnapshotModel(models.Model):
    snapshot = DTOJSONField(schema=OrderSnapshot, default=default_snapshot)

    class Meta:
        abstract = True


class Order(SnapshotModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(max_length=20, default="new")
    text = DTOCharField(schema=OrderSnapshot, max_length=4000, default=default_snapshot)
    binary = DTOBinaryField(schema=OrderSnapshot, default=default_snapshot)
    archived_snapshot = DTOJSONField(schema=OrderSnapshot, null=True, blank=True)


class OrderProxy(Order):
    class Meta:
        proxy = True


class AuditEvent(models.Model):
    details = DTOJSONField(default=dict)


class ValidatedModel(models.Model):
    text = DTOCharField(max_length=16, validators=[text_validator])
    binary = DTOBinaryField(validators=[binary_validator])
    json = DTOJSONField(validators=[mapping_validator])


class OptionalSettings(models.Model):
    required = DTOJSONField()
    optional = DTOJSONField(default=dict, blank=True)
    nullable = DTOJSONField(null=True, blank=True)


class NativeJSONModel(models.Model):
    payload = models.JSONField()


class LengthModel(models.Model):
    text = DTOCharField(max_length=10)
    binary = DTOBinaryField(max_length=10, editable=True)
