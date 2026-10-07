"""Check the E2E database selector without starting external databases."""

from runpy import run_path

import pytest
from django_app import settings as test_settings


def test_sqlite_is_the_default_database(monkeypatch):
    monkeypatch.delenv("DTO_TEST_DB", raising=False)
    database = run_path(test_settings.__file__)["DATABASES"]["default"]
    assert database == {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}


@pytest.mark.parametrize(
    "backend, engine, port",
    [
        ("postgresql", "django.db.backends.postgresql", "55432"),
        ("mysql", "django.db.backends.mysql", "53306"),
        ("mariadb", "django.db.backends.mysql", "53307"),
        ("oracle", "django.db.backends.oracle", "51521"),
    ],
)
def test_external_database_selection(monkeypatch, backend, engine, port):
    monkeypatch.setenv("DTO_TEST_DB", backend)
    database = run_path(test_settings.__file__)["DATABASES"]["default"]
    assert database["ENGINE"] == engine
    if backend == "oracle":
        assert database["NAME"] == f"127.0.0.1:{port}/FREEPDB1"
        assert database["TEST"]["NAME"] == database["NAME"]
    else:
        assert database["HOST"] == "127.0.0.1"
        assert database["PORT"] == port


def test_database_connection_settings_can_be_overridden(monkeypatch):
    monkeypatch.setenv("DTO_TEST_DB", "postgresql")
    monkeypatch.setenv("DTO_TEST_DB_HOST", "db.example")
    monkeypatch.setenv("DTO_TEST_DB_PORT", "5433")
    monkeypatch.setenv("DTO_TEST_DB_PASSWORD", "different-password")
    database = run_path(test_settings.__file__)["DATABASES"]["default"]
    assert database["HOST"] == "db.example"
    assert database["PORT"] == "5433"
    assert database["PASSWORD"] == "different-password"


def test_oracle_connection_overrides_keep_the_test_service(monkeypatch):
    monkeypatch.setenv("DTO_TEST_DB", "oracle")
    monkeypatch.setenv("DTO_TEST_DB_HOST", "oracle.example")
    monkeypatch.setenv("DTO_TEST_DB_PORT", "1522")
    monkeypatch.setenv("DTO_TEST_DB_NAME", "OTHERPDB")
    database = run_path(test_settings.__file__)["DATABASES"]["default"]
    assert database["NAME"] == "oracle.example:1522/OTHERPDB"
    assert database["TEST"]["NAME"] == database["NAME"]


def test_unknown_database_is_rejected(monkeypatch):
    monkeypatch.setenv("DTO_TEST_DB", "unknown")
    with pytest.raises(ValueError, match="Unsupported E2E database"):
        run_path(test_settings.__file__)
