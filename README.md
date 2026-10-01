<p align="center">
    <img src="docs/media/logo.png" style="max-height: 200px; max-width: 200px;" alt="django-dto-field logo"/>
    <br/>
    <b style="font-size: 45;">django-dto-field</b>
    <br/>
    <i>Use your favorite DTO's in Django models</i>
    <br/>
    <br/>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://github.com/skv0zsneg/django-dto-field/actions/workflows/test.yml/badge.svg" alt="PyPi"/>
    </a>
    <a href="https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml" target="_blank">
        <img src="https://github.com/skv0zsneg/django-dto-field/actions/workflows/typing_and_lint.yml/badge.svg" alt="Typing and Linters"/>
    </a>
    <br/>
    <a href="https://pypi.org/project/django-dto-field/" target="_blank">
        <img src="https://img.shields.io/pypi/v/django-dto-field.svg" alt="PyPi"/>
    </a>
    <a href="https://github.com/wemake-services/wemake-python-styleguide" target="_blank">
        <img src="https://img.shields.io/badge/style-wemake-000000.svg" alt="wemake style"/>
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

## Quick start

Install using pip:

```bash
pip install django-dto-field
```

or uv:

```bash
uv add django-dto-field
```

Define your DTO. For example through `dataclass`:

```python
>>> from dataclasses import dataclass

>>> @dataclass
... class Address:
...    city: str

>>> @dataclass
... class Customer:
...    name: str
...    address: Address
```

Create model and add field:

```python
>>> from django.db import models
>>> from django_dto_field.fields.json import DTOJSONField

>>> class Order(models.Model):
...    customer = DTOJSONField(schema=Customer)
```

After migrations you can use it like this:

```python
>>> from myapp.models import Order
>>> from myapp.dto import Address, Customer

>>> order = Order.objects.create(customer=Customer("Alice", Address("London")))
>>> order.refresh_from_db()

>>> assert order.customer == Customer("Alice", Address("London"))
>>> assert isinstance(order.customer.address, Address)

>>> Order.objects.filter(customer__address__city="London")  # Lookups
>>> Order.objects.values_list("customer__address", flat=True)  # Return dictionary
```