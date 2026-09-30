from typing import TYPE_CHECKING, Any

from django.db import models

from django_dto_field.adapters.base import DTO
from django_dto_field.fields.mixin import DTOFieldMixin
from django_dto_field.storage import TextStorage

if TYPE_CHECKING:
    CharField = models.CharField[Any, Any]
else:
    CharField = models.CharField


class DTOCharField(DTOFieldMixin[DTO], CharField):
    """A Django CharField with DTO mixin."""

    storage = TextStorage()
