"""DTOs stored as plain JSON bytes."""

from typing import TYPE_CHECKING, Any

from django.db import models

from django_dto_field.adapters.base import DTO
from django_dto_field.fields.mixin import DTOFieldMixin
from django_dto_field.storage import BinaryStorage

if TYPE_CHECKING:
    BinaryField = models.BinaryField[Any, Any]
else:
    BinaryField = models.BinaryField


class DTOBinaryField(DTOFieldMixin[DTO], BinaryField):
    """A Django BinaryField with DTO mixin."""

    storage = BinaryStorage()
