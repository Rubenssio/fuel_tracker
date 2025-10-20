"""Models for user profiles and preferences."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Stores user-specific preferences for display and localisation."""

    UNIT_KILOMETERS = "km"
    UNIT_MILES = "mi"
    UNIT_LITERS = "L"
    UNIT_GALLONS = "gal"

    DISTANCE_UNIT_CHOICES = [
        (UNIT_KILOMETERS, "Kilometres"),
        (UNIT_MILES, "Miles"),
    ]

    VOLUME_UNIT_CHOICES = [
        (UNIT_LITERS, "Litres"),
        (UNIT_GALLONS, "Gallons"),
    ]

    class EfficiencyUnit(models.TextChoices):
        L_PER_100KM = "l_per_100km", "L/100km"
        MPG = "mpg", "MPG"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    distance_unit = models.CharField(
        max_length=2,
        choices=DISTANCE_UNIT_CHOICES,
        default=UNIT_KILOMETERS,
    )
    volume_unit = models.CharField(
        max_length=3,
        choices=VOLUME_UNIT_CHOICES,
        default=UNIT_LITERS,
    )
    efficiency_unit = models.CharField(
        max_length=16,
        choices=EfficiencyUnit.choices,
        default=EfficiencyUnit.L_PER_100KM,
    )
    timezone = models.CharField(max_length=255, default="UTC")
    utc_offset_minutes = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"Profile for {self.user}"  # pragma: no cover - representation only
