# django-dto-field

[![PyPI](https://img.shields.io/pypi/v/django-dto-field.svg)](https://pypi.org/project/django-dto-field/)
[![Tests](https://github.com/skv0zsneg/django-dto-field/actions/workflows/test.yml/badge.svg)](https://github.com/skv0zsneg/django-dto-field/actions/workflows/test.yml)
[![typing & lint](https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml/badge.svg?event=push)](https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml)

[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)

**Store validated dictionaries and dataclasses directly in Django model fields.**

## Why use it?

Django's `JSONField` stores structured data, but does not reconstruct your typed
objects or validate their annotated members. Applications often repeat that
conversion in model methods, services, and forms.

`django-dto-field` puts that work at the field boundary. Write a DTO, read a DTO,
and keep schema validation consistent across model saves, queryset updates, and
bulk writes. Choose native JSON, text, or binary storage to suit your database.

- Dictionaries work without a schema.
- Dataclasses support nested objects and strict member validation through `msgspec`.
- JSON fields retain Django's key lookups and projections.
- ModelForms display JSON, and Django JSON fixtures round-trip DTO values.
- Explicit adapters provide an extension point for other DTO libraries.

## Install

Requires **Python 3.10+** and **Django 4.2+**.

```bash
pip install django-dto-field
```

No additional entry in `INSTALLED_APPS` is required. Add the fields to your models,
then create and apply migrations as usual.

## Quick start

### Store a dictionary

In your application's `models.py`:

```python
from django.db import models

from django_dto_field.fields.json import DTOJSONField


class Document(models.Model):
    metadata = DTOJSONField(default=dict, blank=True)
```

After migrating, use the field in the Django shell or application code:

```python
from myapp.models import Document

document = Document.objects.create(metadata={"author": "Ada", "tags": ["math"]})
document.refresh_from_db()
assert document.metadata == {"author": "Ada", "tags": ["math"]}

Document.objects.filter(metadata__author="Ada")
Document.objects.values_list("metadata__tags", flat=True)  # Returns lists.
```

Use callable defaults such as `dict` so each instance gets its own value.

### Work with typed, nested objects

Define schema classes at module scope so Django can serialize them in migrations:

```python
from dataclasses import dataclass

from django.db import models

from django_dto_field.fields.json import DTOJSONField


@dataclass
class Address:
    city: str


@dataclass
class Customer:
    name: str
    address: Address


class Order(models.Model):
    customer = DTOJSONField(schema=Customer)
```

Save and retrieve the typed object:

```python
from myapp.models import Address, Customer, Order

order = Order.objects.create(customer=Customer("Alice", Address("London")))
order.refresh_from_db()
assert order.customer == Customer("Alice", Address("London"))

Order.objects.filter(customer__address__city="London")
Order.objects.values_list("customer__address", flat=True)  # Returns dictionaries.
```

Dictionary input is accepted too. `full_clean()` converts it on the model instance:

```python
order = Order(customer={"name": "Bob", "address": {"city": "Paris"}})
order.full_clean()
assert isinstance(order.customer, Customer)
order.save()
```

Invalid annotated members raise Django `ValidationError` during validation or
literal writes—even when Python permits constructing the dataclass:

```python
from django.core.exceptions import ValidationError

try:
    Order.objects.create(customer=Customer("Alice", Address(city=123)))
except ValidationError as error:
    print(error)
```

### Choose a storage field

The schema and adapter options work with all three fields:

| Import | Django base | Stored value |
| --- | --- | --- |
| `django_dto_field.fields.json.DTOJSONField` | `JSONField` | Native JSON, encoded by Django |
| `django_dto_field.fields.char.DTOCharField` | `CharField` | UTF-8 JSON text |
| `django_dto_field.fields.binary.DTOBinaryField` | `BinaryField` | UTF-8 JSON bytes |

```python
from django_dto_field.fields.binary import DTOBinaryField
from django_dto_field.fields.char import DTOCharField

# Inside a model definition:
summary = DTOCharField(max_length=2000, default=dict, blank=True)
archive = DTOBinaryField(schema=Customer, null=True, blank=True)
```

`DTOCharField.max_length` measures the serialized text. `DTOBinaryField` retains
Django's `editable=False` default. Package initializers do not re-export classes;
use the module paths above.

## Behavior to know

- **Validation timing:** attribute assignment does not validate. Conversion and
  literal writes validate the schema, including `update()` and bulk writes.
  Call `full_clean()` for Django field validators; `save()` does not run them all.
- **In-memory values:** saving dictionary input prepares it for storage without
  replacing the attribute. Use `full_clean()` or `refresh_from_db()` to obtain a DTO.
- **Field validators:** receive the storage value—text, bytes, or a JSON-compatible
  mapping. `null` and `blank` retain Django semantics.
- **JSON lookups:** partial/scalar operands bypass whole-DTO validation. Key
  projections return native JSON values, not partial dataclasses.
- **Nulls:** `None` stores SQL NULL when permitted. `DTOJSONField` also supports
  explicit JSON null through Django's `Value(None, output_field=...)`.
- **SQL expressions:** arbitrary database expressions are not schema-validated
  before execution; complete values are validated when read back.
- **Schema changes:** changing a schema does not rewrite existing data. Plan a
  data migration when stored values no longer satisfy the new schema.

## Extend DTO support

Dicts and dataclasses are built in. Pydantic, Marshmallow, and other integrations
can be added with an importable adapter class; they are not bundled today.

```python
from django_dto_field.fields.json import DTOJSONField
from myapp.dto import MyAdapter, MySchema

payload = DTOJSONField(schema=MySchema, adapter=MyAdapter)
```

Implement the `DTOAdapter` protocol from `django_dto_field.adapters.base`:

- `__init__(schema)`: configure and validate the schema.
- `is_instance(instance)`: recognize a DTO using `TypeGuard`.
- `to_data(instance)`: produce a JSON-compatible dictionary.
- `from_data(payload)`: validate a complete dictionary and reconstruct a DTO.

The schema and result classes may differ. Adapters are instantiated per converter
and preserved in migrations, with no global registry. Translate integration
errors into library exceptions from `django_dto_field.exceptions.base`.
At the Django boundary, these become `DTOFieldError` from
`django_dto_field.exceptions.django`, which also inherits Django `ValidationError`.

See the [test adapters](tests/e2e/dict_field/adapters.py) for small working examples.

## Help and contribute

Questions, bug reports, documentation improvements, and feature proposals are
welcome in the [issue tracker](https://github.com/skv0zsneg/django-dto-field/issues).
For bugs, include a minimal example, your Python/Django versions, and the expected
and actual behavior.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, and pull request guidance.
The project uses unit, property-based, and Django integration tests with 100%
statement/branch coverage, plus Ruff, WPS, and strict mypy checks.

## License

Available under the [MIT license](LICENSE).
