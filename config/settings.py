"""Minimal Django settings for the bootstrap service."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-devonly")

DEBUG = os.environ.get("DJANGO_DEBUG", "0").lower() in {"1", "true", "yes", "on"}

_default_allowed_hosts = "localhost,127.0.0.1,0.0.0.0"
ALLOWED_HOSTS: list[str] = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", _default_allowed_hosts).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES: list[dict[str, object]] = []

WSGI_APPLICATION = "config.wsgi.application"

DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "app"),
        "USER": os.environ.get("POSTGRES_USER", "app"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "change-me-devonly"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security-related toggles (disabled for local development).
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "false").lower() == "true"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "false").lower() == "true"
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "false").lower() == "true"
