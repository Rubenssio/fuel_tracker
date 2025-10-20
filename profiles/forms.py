"""Forms for editing user profile preferences."""
from __future__ import annotations

import re

from django import forms

from .models import Profile


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def _build_offset_choices() -> list[tuple[int, str]]:
    choices: list[tuple[int, str]] = []
    for hour in range(-12, 15):
        label = f"UTC{hour:+d}"
        choices.append((hour * 60, label))
    return choices


_UTC_OFFSET_CHOICES = _build_offset_choices()


class ProfileForm(forms.ModelForm):
    """Allow users to update their profile preferences."""

    utc_offset_minutes = forms.TypedChoiceField(
        choices=_UTC_OFFSET_CHOICES,
        coerce=int,
        label="Timezone offset",
    )
    efficiency_unit = forms.ChoiceField(
        choices=Profile.EfficiencyUnit.choices,
        label="Efficiency unit",
    )

    class Meta:
        model = Profile
        fields = [
            "display_name",
            "currency",
            "distance_unit",
            "volume_unit",
            "efficiency_unit",
            "utc_offset_minutes",
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

    def clean_efficiency_unit(self) -> str:
        efficiency_unit = self.cleaned_data["efficiency_unit"]
        valid_units = {choice for choice, _ in Profile.EfficiencyUnit.choices}
        if efficiency_unit not in valid_units:
            raise forms.ValidationError("Select a valid efficiency unit.")
        return efficiency_unit

    def save(self, commit: bool = True) -> Profile:
        profile: Profile = super().save(commit=False)
        profile.timezone = "UTC"
        if commit:
            profile.save()
            self.save_m2m()
        return profile
