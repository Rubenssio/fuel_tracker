"""Database models for the core app."""
from __future__ import annotations

from django.db import models


class BaselineSeed(models.Model):
    """Sentinel row used to confirm the baseline seed ran."""

    SENTINEL_PK = 1

    label = models.CharField(max_length=64, default="baseline", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Baseline seed"
        verbose_name_plural = "Baseline seeds"

    def __str__(self) -> str:  # pragma: no cover - representation helper
        return f"BaselineSeed<{self.pk}>"
