import os

import django

SECRET_KEY = "tests-only-secret"
INSTALLED_APPS = ["django.contrib.contenttypes", "dict_field"]
MIGRATION_MODULES = {"dict_field": None}

BACKENDS = {
    "postgresql": ("django.db.backends.postgresql", "55432", "dto_test"),
    "mysql": ("django.db.backends.mysql", "53306", "root"),
    "mariadb": ("django.db.backends.mysql", "53307", "root"),
    "oracle": ("django.db.backends.oracle", "51521", "system"),
}
backend = os.environ.get("DTO_TEST_DB", "sqlite")
if backend == "sqlite":
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
    }
else:
    if backend not in BACKENDS:
        raise ValueError(f"Unsupported E2E database: {backend}")
    engine, port, user = BACKENDS[backend]
    host = os.environ.get("DTO_TEST_DB_HOST", "127.0.0.1")
    port = os.environ.get("DTO_TEST_DB_PORT", port)
    name = os.environ.get(
        "DTO_TEST_DB_NAME", "FREEPDB1" if backend == "oracle" else "dto_test"
    )
    database = {
        "ENGINE": engine,
        "NAME": name,
        "USER": os.environ.get("DTO_TEST_DB_USER", user),
        "PASSWORD": os.environ.get("DTO_TEST_DB_PASSWORD", "dto_test_password"),
        "HOST": host,
        "PORT": port,
    }
    if backend in ("mysql", "mariadb"):
        database["OPTIONS"] = {"charset": "utf8mb4"}
    if backend == "oracle":
        client_lib_dir = os.environ.get("DTO_ORACLE_CLIENT_LIB_DIR")
        if client_lib_dir and django.VERSION[:2] == (4, 2):
            import cx_Oracle

            cx_Oracle.init_oracle_client(lib_dir=client_lib_dir)
        database.update(
            NAME=f"{host}:{port}/{name}",
            HOST="",
            PORT="",
            TEST={"NAME": f"{host}:{port}/{name}"},
        )
    DATABASES = {"default": database}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
