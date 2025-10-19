from __future__ import annotations

from decimal import Decimal

from django import forms

from profiles.models import Profile
from profiles.units import gallons_to_liters, miles_to_km
from vehicles.models import Vehicle

from .models import FillUp


class FillUpForm(forms.ModelForm):
    class Meta:
        model = FillUp
        fields = [
            "vehicle",
            "date",
            "odometer_km",
            "station_name",
            "fuel_brand",
            "fuel_grade",
            "liters",
            "total_amount",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "odometer_km": forms.NumberInput(attrs={"min": 1}),
            "liters": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "total_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "total_amount": "Total amount paid in your selected currency.",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.profile: Profile | None = None
        super().__init__(*args, **kwargs)

        if user is not None:
            defaults = {
                "currency": "USD",
                "distance_unit": Profile.UNIT_KILOMETERS,
                "volume_unit": Profile.UNIT_LITERS,
                "timezone": "UTC",
                "utc_offset_minutes": 0,
                "efficiency_unit": Profile.EfficiencyUnit.L_PER_100KM,
            }
            self.profile, _ = Profile.objects.get_or_create(user=user, defaults=defaults)

        distance_unit = Profile.UNIT_KILOMETERS
        volume_unit = Profile.UNIT_LITERS
        if self.profile is not None:
            distance_unit = self.profile.distance_unit
            volume_unit = self.profile.volume_unit

        odometer_label = "km" if distance_unit == Profile.UNIT_KILOMETERS else "mi"
        odometer_help = (
            "kilometers" if distance_unit == Profile.UNIT_KILOMETERS else "miles"
        )
        liters_label = "L" if volume_unit == Profile.UNIT_LITERS else "gal"
        liters_help = "liters" if volume_unit == Profile.UNIT_LITERS else "gallons"

        self.fields["odometer_km"].label = f"Odometer ({odometer_label})"
        self.fields["odometer_km"].help_text = (
            f"Enter the odometer reading in {odometer_help}."
        )
        self.fields["liters"].label = f"Volume ({liters_label})"
        self.fields["liters"].help_text = f"Fuel volume in {liters_help}."

        vehicle_field = self.fields.get("vehicle")
        if vehicle_field is not None:
            queryset = Vehicle.objects.none()
            if user is not None:
                queryset = Vehicle.objects.filter(user=user)
            vehicle_field.queryset = queryset

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data:
            return cleaned_data

        profile = self.profile
        if profile is not None:
            odometer_value = cleaned_data.get("odometer_km")
            if odometer_value is not None and profile.distance_unit == Profile.UNIT_MILES:
                converted = miles_to_km(float(odometer_value))
                cleaned_data["odometer_km"] = int(round(converted))

            liters_value = cleaned_data.get("liters")
            if liters_value is not None and profile.volume_unit == Profile.UNIT_GALLONS:
                liters_float = gallons_to_liters(float(liters_value))
                converted_decimal = Decimal(str(liters_float)).quantize(Decimal("0.01"))
                cleaned_data["liters"] = converted_decimal

        def _normalize(value: str | None) -> str:
            value = (value or "").strip()
            if not value:
                return ""
            return " ".join(value.split())

        cleaned_data["fuel_brand"] = _normalize(cleaned_data.get("fuel_brand"))
        cleaned_data["fuel_grade"] = _normalize(cleaned_data.get("fuel_grade"))
        cleaned_data["station_name"] = _normalize(cleaned_data.get("station_name"))

        return cleaned_data
