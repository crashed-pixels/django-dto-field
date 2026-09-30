from typing import Any


class JSONStorage:
    """The default storage for DTO.

    Comes with :class:`DTOJSONField`.
    """

    def encode(self, payload: dict[str, Any]) -> object:
        """Just return the pure mapping for comparing with :class:`JSONField`."""
        return payload

    def decode(self, raw: object) -> object:
        """Accept a value already decoded by Django."""
        return raw
