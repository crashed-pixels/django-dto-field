from typing import Any

from django_dto_field.storage.binary import BinaryStorage
from django_dto_field.storage.json import JSONStorage


class TextStorage(JSONStorage):
    """Using to encode and decode JSON mapping same as :class:`BinaryStorage`
    to and from string using UTF-8 encoding.

    Comes with :class:`DTOCharField`.
    """

    def encode(self, payload: dict[str, Any]) -> str:
        """Encode a mapping as JSON text."""
        return BinaryStorage().encode(payload).decode("utf-8")

    def decode(self, raw: object) -> object:
        """Decode the JSON text."""
        return BinaryStorage().decode(raw)
