"""Store DTO mappings as UTF-8 JSON bytes in Django binary fields."""

from typing import TYPE_CHECKING, Any

from django.db import models

from django_dto_field.adapters.base import DTO
from django_dto_field.fields.mixin import DTOFieldMixin
from django_dto_field.storage.binary import BinaryStorage

if TYPE_CHECKING:
    BinaryField = models.BinaryField[Any, Any]
else:
    BinaryField = models.BinaryField


class DTOBinaryField(DTOFieldMixin[DTO], BinaryField):
    """Combine DTO conversion with Django's binary field.

    Values are plain UTF-8 JSON bytes. Django's ``editable=False`` default is
    retained. See :class:`~django_dto_field.fields.mixin.DTOFieldMixin` for options.
    """

    storage = BinaryStorage()
