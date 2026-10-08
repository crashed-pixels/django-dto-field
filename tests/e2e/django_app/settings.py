import os

SECRET_KEY = "tests-only-secret"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dict_field",
]
MIGRATION_MODULES = {"dict_field": None}
ROOT_URLCONF = "django_app.urls"
ALLOWED_HOSTS = ["testserver"]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
STATIC_URL = "/static/"

BACKENDS = {
    "postgresql": ("django.db.backends.postgresql", "55432", "dto_test"),
    "mysql": ("django.db.backends.mysql", "53306", "root"),
    "mariadb": ("django.db.backends.mysql", "53307", "root"),
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
    name = os.environ.get("DTO_TEST_DB_NAME", "dto_test")
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
    DATABASES = {"default": database}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
