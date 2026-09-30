"""Test-only DTO integration: its schema and result are unrelated classes."""

from typing import Any, TypeGuard

from django_dto_field.adapters.base import DTOAdapter
from django_dto_field.exceptions.base import DTOValidationError, SchemaError


class Message:
    def __init__(self, identifier: int) -> None:
        self.identifier = identifier

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Message) and self.identifier == other.identifier


class MessageSchema:
    minimum = 1

    @classmethod
    def load(cls, payload: dict[str, Any]) -> Message:
        identifier = payload.get("identifier")
        if type(identifier) is not int or identifier < cls.minimum:
            raise ValueError("identifier must be a positive integer")
        return Message(identifier)


class MessageAdapter:
    def __init__(self, schema: type[Any]) -> None:
        if not issubclass(schema, MessageSchema):
            raise SchemaError("Expected a MessageSchema class")
        self.schema = schema

    def is_instance(self, instance: object) -> TypeGuard[Message]:
        return isinstance(instance, Message)

    def to_data(self, instance: Message) -> dict[str, Any]:
        return {"identifier": instance.identifier}

    def from_data(self, payload: dict[str, Any]) -> Message:
        try:
            return self.schema.load(payload)
        except ValueError as error:
            raise DTOValidationError(str(error)) from error


class MappingAdapter:
    """A schema library may load dictionaries rather than custom DTO classes."""

    def __init__(self, schema: type[Any]) -> None:
        self.messages = MessageAdapter(schema)

    def is_instance(self, instance: object) -> TypeGuard[dict[str, Any]]:
        return isinstance(instance, dict)

    def to_data(self, instance: dict[str, Any]) -> dict[str, Any]:
        return instance

    def from_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.messages.to_data(self.messages.from_data(payload))


# Structural typing: adapter authors aren't required to inherit our protocol.
message_adapter: type[DTOAdapter[Message]] = MessageAdapter
mapping_adapter: type[DTOAdapter[dict[str, Any]]] = MappingAdapter
