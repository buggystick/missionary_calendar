"""Django settings for calendar_site project."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes"}

ALLOWED_HOSTS_ENV = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",") if host.strip()] if ALLOWED_HOSTS_ENV else []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "calendar_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "calendar_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "calendar_site.wsgi.application"
ASGI_APPLICATION = "calendar_site.asgi.application"


def _database_from_env(url: str) -> Dict[str, Any]:
    """Parse a database configuration from a DATABASE_URL string."""
    try:
        import dj_database_url  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        dj_database_url = None

    if dj_database_url is not None:
        return dj_database_url.parse(url, conn_max_age=600)

    parsed = urlparse(url)
    scheme = parsed.scheme

    if scheme in {"sqlite", "sqlite3"}:
        path = parsed.path or ""
        if path.startswith("/"):
            path = path[1:]
        if path in {"", ":memory:"}:
            name = ":memory:"
        else:
            name = str((BASE_DIR / path).resolve())
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name,
        }

    raise ImproperlyConfigured(
        "DATABASE_URL is set but dj_database_url is not installed to parse non-sqlite databases."
    )


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": _database_from_env(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


if importlib.util.find_spec("django_htmx") is not None:
    INSTALLED_APPS.append("django_htmx")
    MIDDLEWARE.append("django_htmx.middleware.HtmxMiddleware")
