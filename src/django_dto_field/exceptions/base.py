"""Define library errors independent of Django validation."""


class DTOError(Exception):
    """Base exception for all library-defined failures.

    Catch this class to handle conversion and storage failures independently of
    Django. Its subclasses retain their original failure as ``__cause__`` when
    translating errors from another library.
    """


class SchemaError(DTOError):
    """Report a schema unsupported by the selected adapter.

    Raised when an adapter cannot configure the supplied ``schema`` class.
    """


class SerializationError(DTOError):
    """Report data that cannot be encoded or decoded in the storage format.

    Used for unsupported values, malformed JSON, and incompatible buffer types.
    """


class DTOValidationError(DTOError):
    """Report a DTO instance or mapping that violates its schema.

    Validation concerns DTO structure and members, rather than Django's
    ``null``, ``blank``, or field-validator rules.
    """
