SECRET_KEY = "tests-only-secret"
INSTALLED_APPS = ["django.contrib.contenttypes", "dict_field"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
