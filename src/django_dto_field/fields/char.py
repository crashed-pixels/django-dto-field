"""Store DTO mappings as JSON text in Django character fields."""

from typing import TYPE_CHECKING, Any

from django.db import models

from django_dto_field.adapters.base import DTO
from django_dto_field.fields.mixin import DTOFieldMixin
from django_dto_field.storage.text import TextStorage

if TYPE_CHECKING:
    CharField = models.CharField[Any, Any]
else:
    CharField = models.CharField


class DTOCharField(DTOFieldMixin[DTO], CharField):
    """Combine DTO conversion with Django's character field.

    ``max_length`` measures serialized JSON text. Schema and adapter options are
    described by :class:`~django_dto_field.fields.mixin.DTOFieldMixin`.
    """

    storage = TextStorage()
