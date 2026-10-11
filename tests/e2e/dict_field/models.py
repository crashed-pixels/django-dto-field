from dataclasses import dataclass

from django.db import models

from dict_field.adapters import MappingAdapter, MessageAdapter, MessageSchema
from dict_field.schemas import OrderSnapshot, default_snapshot
from dict_field.validators import binary_validator, mapping_validator
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.json import DTOField


@dataclass
class Address:
    city: str


@dataclass
class UserDTO:
    identifier: int
    address: Address


class DictModel(models.Model):
    binary = DTOBinaryField(default=dict, blank=True)
    json = DTOField(default=dict, blank=True)


class DataclassModel(models.Model):
    binary = DTOBinaryField(schema=UserDTO)
    json = DTOField(schema=UserDTO)


class OptOutModel(models.Model):
    binary = DTOBinaryField(schema=UserDTO, validate_on_assignment=False)
    json = DTOField(schema=UserDTO, validate_on_assignment=False)


class NullableModel(models.Model):
    binary = DTOBinaryField(schema=UserDTO, null=True, blank=True)
    json = DTOField(schema=UserDTO, null=True, blank=True)


class CustomModel(models.Model):
    binary = DTOBinaryField(schema=MessageSchema, adapter=MessageAdapter)
    json = DTOField(schema=MessageSchema, adapter=MessageAdapter)


class MappingModel(models.Model):
    binary = DTOBinaryField(schema=MessageSchema, adapter=MappingAdapter)
    json = DTOField(schema=MessageSchema, adapter=MappingAdapter)


class Customer(models.Model):
    name = models.CharField(max_length=100)


class SnapshotModel(models.Model):
    snapshot = DTOField(schema=OrderSnapshot, default=default_snapshot)

    class Meta:
        abstract = True


class Order(SnapshotModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(max_length=20, default="new")
    binary = DTOBinaryField(schema=OrderSnapshot, default=default_snapshot)
    archived_snapshot = DTOField(schema=OrderSnapshot, null=True, blank=True)


class OrderProxy(Order):
    class Meta:
        proxy = True


class AuditEvent(models.Model):
    details = DTOField(default=dict)


class ValidatedModel(models.Model):
    binary = DTOBinaryField(validators=[binary_validator])
    json = DTOField(validators=[mapping_validator])


class OptionalSettings(models.Model):
    required = DTOField()
    optional = DTOField(default=dict, blank=True)
    nullable = DTOField(null=True, blank=True)


class NativeJSONModel(models.Model):
    payload = models.JSONField()


class LengthModel(models.Model):
    binary = DTOBinaryField(max_length=10, editable=True)
