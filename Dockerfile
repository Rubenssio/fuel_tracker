FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY manage.py ./
COPY config ./config
COPY core ./core

RUN pip install --no-cache-dir "Django==4.2.11" "psycopg[binary]==3.1.18"

USER app

CMD ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py seed_baseline && python manage.py runserver 0.0.0.0:8000"]
