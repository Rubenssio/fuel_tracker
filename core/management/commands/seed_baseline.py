"""Management command to ensure the baseline sentinel data exists."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import BaselineSeed


class Command(BaseCommand):
    help = "Ensures the baseline sentinel record exists."

    def handle(self, *args, **options):  # type: ignore[override]
        BaselineSeed.objects.update_or_create(
            pk=BaselineSeed.SENTINEL_PK,
            defaults={"label": "baseline"},
        )
        self.stdout.write(self.style.SUCCESS("Baseline seed ensured."))
