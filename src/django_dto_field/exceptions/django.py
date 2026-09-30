from collections.abc import Generator
from contextlib import contextmanager

from django.core.exceptions import ValidationError

from django_dto_field.exceptions.base import DTOError


class DTOFieldError(ValidationError, DTOError):
    """Invalid DTO input or persisted data at the Django boundary."""


@contextmanager
def field_errors() -> Generator[None]:
    """Translate library failures while preserving their original cause."""
    try:
        yield
    except DTOError as error:
        raise DTOFieldError(str(error), code="invalid_dto") from error
