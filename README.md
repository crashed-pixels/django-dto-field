<p align="center">
    <br/>
    <img src="https://github.com/crashed-pixels/django-dto-field/blob/dev/docs/media/logo.png?raw=true" width="700" alt="django-dto-field logo"/>
    <br/>
    <br/>
    <a href="https://github.com/crashed-pixels/django-dto-field/actions/workflows/test.yml" target="_blank">
        <img src="https://github.com/crashed-pixels/django-dto-field/actions/workflows/test.yml/badge.svg" alt="Tests"/>
    </a>
    <a href="https://github.com/crashed-pixels/django-dto-field/actions/workflows/typing_and_lint.yml" target="_blank">
        <img src="https://github.com/crashed-pixels/django-dto-field/actions/workflows/typing_and_lint.yml/badge.svg" alt="Typing and Linters"/>
    </a>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://img.shields.io/pypi/v/django-dto-field.svg" alt="PyPI version"/>
    </a>
    <br/>
    <a href="https://github.com/wemake-services/wemake-python-styleguide" target="_blank">
        <img src="https://img.shields.io/badge/style-wemake-000000.svg" alt="wemake style"/>
    </a>
    <a href="https://github.com/crashed-pixels" target="_blank">
        <img src="https://img.shields.io/badge/crashed-pixels-green?style=flat" alt="crashed-pixels"/>
    </a>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://img.shields.io/pypi/dm/django-dto-field" alt="Monthly PyPI downloads"/>
    </a>
</p>

For Django developers who want to store structures in model fields but do not want to manually serialize dictionaries into DTO objects and vice versa. `django-dto-field` hide converting logic and gives you original Django interface.

## Table of contents

1. [Quick start](#quick-start)
2. [No schema is set](#no-schema-is-set)
3. [Supported DTO types](#supported-dto-types)
4. [Django Fields](#django-fields)
    1. [DTOField](#dtofield)
    2. [DTOBinaryField](#dtobinaryfield)
5. [Supported versions and databases](#supported-versions-and-databases)
6. [Help and contribute](#help-and-contribute)
7. [License](#license)

## Quick start

Django itself have a `JSONField` for storing structures in JSON comparable format. But it have some restrictions. Let's see it through comparing `JSONField` and `DTOField` on one task.

First, install the package:

```bash
pip install django-dto-field
```

Suppose you have these nested dataclass DTOs:

```python
# app/my_dto.py

from dataclasses import dataclass

@dataclass
class Address:
    city: str

@dataclass
class Customer:
    name: str
    address: Address
```

To store a customer in a Django model, let's compare Django's built-in `JSONField` with `django-dto-field`'s `DTOField`:

```python
# app/models.py

from django.db.models import JSONField, Model
from django_dto_field.fields.json import DTOField
from app.my_dto import Customer

class DjangoOrder(Model):
    customer = JSONField()

class DTOOrder(Model):
    customer = DTOField(schema=Customer)
```

Add `app` to `INSTALLED_APPS`, create and apply migrations, then open the Django shell with `./manage.py shell`.

Create a customer to store:

```python
>>> from app.my_dto import Address, Customer
>>> customer = Customer(name="Alice", address=Address(city="London"))
```

Let's try to store and load it with `JSONField`.

```python
>>> from dataclasses import asdict
>>> from app.models import DjangoOrder

>>> # JSONField requires a JSON-compatible value, so convert the dataclass first.
>>> order = DjangoOrder.objects.create(customer=asdict(customer))
>>> order.refresh_from_db()

>>> # Loading returns dictionaries, including nested values.
>>> assert isinstance(order.customer, dict)
>>> assert isinstance(order.customer["address"], dict)
>>> assert order.customer["address"]["city"] == "London"

>>> # Standard Django JSON lookups work.
>>> DjangoOrder.objects.filter(customer__address__city="London")

>>> # Reconstruct the nested dataclasses manually to restore attribute access.
>>> payload = order.customer
>>> customer = Customer(
...     name=payload["name"],
...     address=Address(**payload["address"]),
... )

>>> # JSONField does not enforce the dataclass schema.
>>> invalid_customer = {
...     "name": "Alice",
...     "address": {"city": 123},  # city should be a string
... }

>>> # Valid JSON is accepted even though city has the wrong type.
>>> DjangoOrder.objects.create(customer=invalid_customer)
```

Now let's do the same with `django-dto-field`.

```python
>>> from app.models import DTOOrder

>>> # DTOField handles dataclass conversion automatically.
>>> order = DTOOrder.objects.create(customer=customer)
>>> order.refresh_from_db()

>>> # Loading automatically reconstructs the nested dataclasses.
>>> assert isinstance(order.customer, Customer)
>>> assert isinstance(order.customer.address, Address)
>>> assert order.customer.address.city == "London"

>>> # The same Django JSON lookups work.
>>> DTOOrder.objects.filter(customer__address__city="London")

>>> # Invalid data raises a Django ValidationError during model construction by default.
>>> from django.core.exceptions import ValidationError
>>> invalid_customer = {
...     "name": "Alice",
...     "address": {"city": 123},  # city should be a string
... }

>>> try:
...     # DTOField also accepts dictionaries and validates them against the dataclass schema.
...     DTOOrder.objects.create(customer=invalid_customer)
... except ValidationError:
...     print("The customer data does not match the schema!")
```

As a result, `django-dto-field` provides:
- Familiar Django model and query interfaces;
- Less conversion boilerplate, so you can focus on business logic;
- Runtime schema validation to catch invalid data early.

When might you prefer Django's `JSONField`? If your data structure changes frequently and you do not need typed objects or schema validation, plain dictionaries may be simpler than maintaining a schema.

## No schema is set

Omit `schema` on any DTO field to store dictionaries with JSON-compatible values.
Loading returns a `dict`. Add the `Event` model below to `app/models.py`, create
and apply migrations, then run the database operations in the Django shell.

```python
>>> from django.db import models
>>> from django_dto_field.fields.json import DTOField
>>> class Event(models.Model):
...     details = DTOField(default=dict)

>>> from app.models import Event
>>> event = Event.objects.create(details={"kind": "signup"})
>>> event.refresh_from_db()
>>> event.details
{'kind': 'signup'}
```

## Supported DTO types

The default adapter supports dataclasses and dictionaries. Dataclasses require an explicit, importable `schema` class. Dictionaries have no declared member schema, but the field still checks that they can be converted to JSON-compatible data.

If you would like support for another DTO type, please open an issue in the [issue tracker](https://github.com/crashed-pixels/django-dto-field/issues). You can also provide an importable `adapter=` class implementing `DTOAdapter` from `django_dto_field.adapters.base`. Pull requests are welcome!

## Django Fields

The library wraps Django's JSON and binary model fields to add DTO conversion and validation. Each field
accepts its Django base field's options, such as `null` and `blank`.

Schema validation runs on assignment by default, including model construction.
Set `DTOField(schema=Customer, validate_on_assignment=False)` on a field to defer validation until conversion
or saving. In-place changes to a DTO or dictionary are checked on save.
SQL expressions bypass literal-value validation. DTO results are checked on load.
Call `full_clean()` to run Django field validators; they receive the stored
mapping or bytes.

For optional form input, use `null=True, blank=True`. With the default dictionary
schema and `blank=True`, submit `{}` to store an empty dictionary;
`blank=True` alone does not allow SQL NULL.

### `DTOField`

`DTOField` wraps Django's `JSONField` to store DTOs as native JSON. You are
already familiar with this field from the [quick start](#quick-start).

- Stores mappings as native JSON in the database.
- Inherits from Django's `JSONField`.
- Supports Django JSON key lookups.
- Projected keys return native values, not DTOs.
- JSON key projections follow Django's backend behavior. On SQLite, use
`KeyTextTransform` when strings such as `"0"` or `"null"` must remain strings.

### `DTOBinaryField`

Define this model in `app/models.py`:

```python
>>> from django.db import models
>>> from django_dto_field.fields.binary import DTOBinaryField
>>> from app.my_dto import Customer
>>> class StoredOrder(models.Model):
...     customer_bytes = DTOBinaryField(schema=Customer)
```

- Stores UTF-8 JSON bytes in the database.
- Inherits from Django's `BinaryField`.
- Is not editable by default, as with Django's `BinaryField`; set `editable=True` to include it in ModelForms.

## Supported versions and databases

- Python 3.10–3.14.
- Django 5.2 (Python 3.10–3.14) and 6.0–6.1
  (Python 3.12–3.14).
- SQLite, PostgreSQL, MySQL, and MariaDB.

## Help and contribute

Have a question, spotted a bug, or want a new DTO integration? We'd love to hear
from you in the [issue tracker](https://github.com/crashed-pixels/django-dto-field/issues).
For bugs, include a minimal example, your Python/Django versions, and the expected
and actual behavior.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, and pull request guidance.
Small improvements count too—clearer examples, documentation fixes, and tests
are all welcome.
The project uses unit, property-based, and Django integration tests with 100%
statement/branch coverage, plus Ruff, WPS, and strict mypy checks.

## License

Available under the [MIT license](LICENSE).
