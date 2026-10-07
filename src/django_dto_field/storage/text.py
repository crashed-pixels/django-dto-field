"""Encode and decode JSON text for character field storage."""

from typing import Any

from django_dto_field.storage.binary import BinaryStorage
from django_dto_field.storage.json import JSONStorage


class TextStorage(JSONStorage):
    """Convert JSON mappings to text using the shared UTF-8 codec.

    Used by :class:`~django_dto_field.fields.char.DTOCharField`. Decoding
    accepts both text and binary values returned by database drivers.
    """

    _binary_storage = BinaryStorage()

    def encode(self, payload: dict[str, Any]) -> str:
        """Encode a mapping as JSON text."""
        return self._binary_storage.encode(payload).decode("utf-8")

    def decode(self, raw: object) -> object:
        """Decode JSON text or binary data."""
        return self._binary_storage.decode(raw)
