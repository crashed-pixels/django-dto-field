"""Importable order schemas used by application and historical-model tests."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID


class Delivery(Enum):
    STANDARD = "standard"
    EXPRESS = "express"


@dataclass(frozen=True, slots=True)
class LineItem:
    sku: str
    quantity: int


@dataclass
class OrderSnapshot:
    customer: str
    items: list[LineItem]
    reference: UUID
    placed_at: datetime
    delivery_on: date
    delivery: Delivery = Delivery.STANDARD
    note: str | None = None
    tags: list[str] = field(default_factory=list)


def default_snapshot():
    return OrderSnapshot(
        customer="Alice",
        items=[LineItem("book", 2)],
        reference=UUID("12345678-1234-5678-1234-567812345678"),
        placed_at=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        delivery_on=date(2026, 1, 3),
    )


@dataclass
class Preferences:
    theme: str
    notifications: bool = True


@dataclass
class RequiredPreferences:
    theme: str
    locale: str


@dataclass
class NumericPreferences:
    theme: int
