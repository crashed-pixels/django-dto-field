import pytest

from dict_field.models import Customer, Order
from dict_field.schemas import default_snapshot


@pytest.fixture
def snapshot():
    return default_snapshot()


@pytest.fixture
def order(db):
    return Order.objects.create(customer=Customer.objects.create(name="Alice"))
