"""Encode and decode JSON text for character field storage."""

from typing import Any

from django_dto_field.storage.binary import BinaryStorage
from django_dto_field.storage.json import JSONStorage


class TextStorage(JSONStorage):
    """Convert JSON mappings to text using the shared UTF-8 codec.

    Used by :class:`~django_dto_field.fields.char.DTOCharField`. Encoding delegates
    to :class:`~django_dto_field.storage.binary.BinaryStorage` before decoding
    the result as UTF-8 text.
    """

    def encode(self, payload: dict[str, Any]) -> str:
        """Encode a mapping as JSON text."""
        return BinaryStorage().encode(payload).decode("utf-8")

    def decode(self, raw: object) -> object:
        """Decode the JSON text."""
        return BinaryStorage().decode(raw)
