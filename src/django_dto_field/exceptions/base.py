class DTOError(Exception):
    """Base exception for django-dto-field."""


class SchemaError(DTOError):
    """The requested DTO schema is unsupported."""


class SerializationError(DTOError):
    """A value cannot be represented in the storage format."""


class DTOValidationError(DTOError):
    """A value does not satisfy its DTO schema."""
