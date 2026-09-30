from dataclasses import dataclass

from django.db import models

from dict_field.adapters import MessageAdapter, MessageSchema
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


class NullableModel(models.Model):
    text = DTOCharField(schema=UserDTO, max_length=1000, null=True, blank=True)
    binary = DTOBinaryField(schema=UserDTO, null=True, blank=True)
    json = DTOJSONField(schema=UserDTO, null=True, blank=True)


class CustomModel(models.Model):
    text = DTOCharField(schema=MessageSchema, adapter=MessageAdapter, max_length=1000)
    binary = DTOBinaryField(schema=MessageSchema, adapter=MessageAdapter)
    json = DTOJSONField(schema=MessageSchema, adapter=MessageAdapter)
