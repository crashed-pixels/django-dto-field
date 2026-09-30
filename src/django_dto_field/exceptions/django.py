"""Translate internal failures at the Django boundary, retaining their causes."""

from collections.abc import Generator
from contextlib import contextmanager

from django.core.exceptions import ValidationError

from django_dto_field.exceptions.base import DTOError


class DTOFieldError(ValidationError, DTOError):
    """Expose library failures as Django validation errors.

    Inherits both :class:`django.core.exceptions.ValidationError` and
    :class:`~django_dto_field.exceptions.base.DTOError`. Internal failures are
    translated by :func:`field_errors` with their original ``__cause__`` retained.
    """


@contextmanager
def field_errors() -> Generator[None]:
    """Translate library failures while preserving their original cause."""
    try:
        yield
    except DTOError as error:
        raise DTOFieldError(str(error), code="invalid_dto") from error
