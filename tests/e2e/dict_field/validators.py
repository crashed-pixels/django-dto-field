"""Validators assert that model validation receives storage-shaped values."""

from django.core.exceptions import ValidationError


def mapping_validator(value):
    if not isinstance(value, dict) or value.get("allowed") is not True:
        raise ValidationError("Expected an allowed mapping.")


def text_validator(value):
    if not isinstance(value, str) or value != '{"allowed":true}':
        raise ValidationError("Expected allowed JSON text.")


def binary_validator(value):
    if not isinstance(value, bytes) or value != b'{"allowed":true}':
        raise ValidationError("Expected allowed JSON bytes.")
