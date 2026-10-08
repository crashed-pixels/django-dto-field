<p align="center">
    <br/>
    <img src="docs/media/logo.png" width="700" alt="django-dto-field logo"/>
    <br/>
    <br/>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://github.com/skv0zsneg/django-dto-field/actions/workflows/test.yml/badge.svg" alt="PyPi"/>
    </a>
    <a href="https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml" target="_blank">
        <img src="https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml/badge.svg" alt="Typing and Linters"/>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://img.shields.io/pypi/v/django-dto-field.svg" alt="PyPi"/>
    </a>
    </a>
    <br/>
    <a href="https://github.com/wemake-services/wemake-python-styleguide" target="_blank">
        <img src="https://img.shields.io/badge/style-wemake-000000.svg" alt="wemake style"/>
    </a>
    <a href="https://github.com/crashed-pixels" target="_blank">
        <img src="https://img.shields.io/badge/crashed-pixels-green?style=flat" alt="wemake style"/>
    </a>
</p>

## Features

- [X] Python `dict` support by default
- [X] Python [dataclasses](https://docs.python.org/3/library/dataclasses.html) support
- [ ] [Pydantic](https://docs.pydantic.dev/) models
- [ ] [Marshmallow](https://marshmallow.readthedocs.io/) schemas
- [ ] [attrs](https://www.attrs.org/) defines
- [X] Storing in BinaryField
- [X] Storing in CharField
- [X] Storing in JSONField
- [X] Lookups for JSONField
- [X] JSONField forms
- [X] Supported MySQL DB
- [X] Supported Postgres DB
- [X] Supported MariaDB

## Quick start

Installing:

```bash
pip install django-dto-field
```

Usage:

```python
>>> from dataclasses import dataclass
>>> from django.db import models
>>> from django_dto_field.fields.json import DTOJSONField


>>> @dataclass  # Define DTO
... class Address:
...    city: str

>>> @dataclass
... class Customer:  # Use nested DTO
...    name: str
...    address: Address


>>> class Order(models.Model):  # Add field to model
...    customer = DTOJSONField(schema=Customer)

>>> order = Order.objects.create(  # Save it
...    customer=Customer("Alice", Address("London"))
... )


>>> order.refresh_from_db()  # Get it
>>> assert order.customer == Customer("Alice", Address("London"))
>>> assert isinstance(order.customer.address, Address)

>>> Order.objects.filter(customer__address__city="London")  # Use lookups
>>> Order.objects.values_list("customer__address", flat=True)  # Return dictionary
```

## Fields

Use `schema=Customer` to store the dataclass from the quick start. Each field
accepts its Django base field's options, such as `null` and `blank`.

| Field | Django base | Stored value |
| --- | --- | --- |
| `DTOJSONField` | `JSONField` | Native JSON |
| `DTOCharField` | `CharField` | JSON text |
| `DTOBinaryField` | `BinaryField` | UTF-8 JSON bytes |

The quick start uses `DTOJSONField`. To store the same DTO as text or bytes:

```python
>>> from django_dto_field.fields.char import DTOCharField
>>> from django_dto_field.fields.binary import DTOBinaryField

>>> class StoredOrder(models.Model):
...     customer_text = DTOCharField(schema=Customer, max_length=500)
...     customer_bytes = DTOBinaryField(schema=Customer)
```

`DTOJSONField` supports Django JSON key lookups; projected keys return native
values, not DTOs. `DTOCharField` requires `max_length`, which limits the serialized
JSON text. `DTOBinaryField` is not editable by default, as with Django's
`BinaryField`.

JSON key projections follow Django's backend behavior. On SQLite, use
`KeyTextTransform` when strings such as `"0"` or `"null"` must remain strings.
For optional form input, use `null=True, blank=True`, or submit `{}` for an empty
dictionary; `blank=True` alone does not allow SQL NULL.

Schema validation runs on assignment by default, including model construction.
Set `validate_on_assignment=False` on a field to defer validation until conversion
or saving. In-place changes to a DTO or dictionary are checked on save.
SQL expressions bypass literal-value validation; DTO results are checked on load.
Call `full_clean()` to run Django field validators; they receive the stored
mapping, text, or bytes.

## Default `dict` DTO

Omit `schema` on any DTO field to store dictionaries with JSON-compatible values.
Loading returns a `dict`.

```python
>>> class Event(models.Model):
...     details = DTOJSONField(default=dict)

>>> event = Event.objects.create(details={"kind": "signup"})
>>> event.refresh_from_db()
>>> event.details
{'kind': 'signup'}
```

## Supported versions and databases

- Python 3.10–3.14.
- Django 5.2 (Python 3.10–3.14) and 6.0–6.1
  (Python 3.12–3.14).
- SQLite, PostgreSQL, MySQL, and MariaDB.

## Help and contribute

Have a question, spotted a bug, or want a new DTO integration? We'd love to hear
from you in the [issue tracker](https://github.com/skv0zsneg/django-dto-field/issues).
For bugs, include a minimal example, your Python/Django versions, and the expected
and actual behavior.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, and pull request guidance.
Small improvements count too—clearer examples, documentation fixes, and tests
are all welcome.
The project uses unit, property-based, and Django integration tests with 100%
statement/branch coverage, plus Ruff, WPS, and strict mypy checks.

## License

Available under the [MIT license](LICENSE).
