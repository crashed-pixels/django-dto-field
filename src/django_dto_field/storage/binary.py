"""Encode and decode UTF-8 JSON bytes for binary field storage."""

from typing import Any

import msgspec

from django_dto_field.exceptions.base import SerializationError
from django_dto_field.storage.json import JSONStorage


class BinaryStorage(JSONStorage):
    """Convert JSON mappings to bytes and accept database buffer representations.

    Used by :class:`~django_dto_field.fields.binary.DTOBinaryField`. Decoding
    accepts strings, bytes, bytearrays, and memoryviews. Codec failures raise
    :class:`~django_dto_field.exceptions.base.SerializationError`.
    """

    def encode(self, payload: dict[str, Any]) -> bytes:
        """Encode a validated JSON mapping."""
        try:
            return msgspec.json.encode(payload)
        except (TypeError, ValueError, RecursionError) as error:
            raise SerializationError(str(error)) from error

    def decode(self, raw: object) -> object:
        """Decode text or binary JSON."""
        if not isinstance(raw, (str, bytes, bytearray, memoryview)):
            raise SerializationError("Expected JSON text or bytes.")
        try:
            return msgspec.json.decode(raw)
        except (TypeError, ValueError) as error:
            raise SerializationError(str(error)) from error
