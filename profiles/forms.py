"""Forms for editing user profile preferences."""
from __future__ import annotations

import re
from zoneinfo import ZoneInfo

from django import forms

from .models import Profile


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class ProfileForm(forms.ModelForm):
    """Allow users to update their profile preferences."""

    class Meta:
        model = Profile
        fields = [
            "display_name",
            "currency",
            "distance_unit",
            "volume_unit",
            "timezone",
        ]

    def clean_currency(self) -> str:
        currency = self.cleaned_data["currency"].strip().upper()
        if not _CURRENCY_RE.match(currency):
            raise forms.ValidationError("Currency must be a 3-letter ISO code.")
        return currency

    def clean_distance_unit(self) -> str:
        distance_unit = self.cleaned_data["distance_unit"]
        valid_units = {choice for choice, _ in Profile.DISTANCE_UNIT_CHOICES}
        if distance_unit not in valid_units:
            raise forms.ValidationError("Select a valid distance unit.")
        return distance_unit

    def clean_volume_unit(self) -> str:
        volume_unit = self.cleaned_data["volume_unit"]
        valid_units = {choice for choice, _ in Profile.VOLUME_UNIT_CHOICES}
        if volume_unit not in valid_units:
            raise forms.ValidationError("Select a valid volume unit.")
        return volume_unit

    def clean_timezone(self) -> str:
        timezone = self.cleaned_data["timezone"].strip()
        try:
            ZoneInfo(timezone)
        except Exception as exc:  # pragma: no cover - depends on system tzdata
            raise forms.ValidationError("Enter a valid IANA timezone.") from exc
        return timezone
