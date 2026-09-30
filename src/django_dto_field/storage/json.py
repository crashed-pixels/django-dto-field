"""Keep JSON-compatible mappings native for Django backend encoding."""

from typing import Any


class JSONStorage:
    """Return native JSON values without additional encoding.

    Used by :class:`~django_dto_field.fields.json.DTOJSONField`. Django's backend
    handles JSON encoding; decoded values pass through unchanged.
    """

    def encode(self, payload: dict[str, Any]) -> object:
        """Return the mapping for Django's JSON adapter."""
        return payload

    def decode(self, raw: object) -> object:
        """Accept a value already decoded by Django."""
        return raw
