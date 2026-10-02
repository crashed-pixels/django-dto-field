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
