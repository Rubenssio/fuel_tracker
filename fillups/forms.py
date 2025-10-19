from __future__ import annotations

from django import forms

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
            "odometer_km": "Enter the odometer reading in kilometers.",
            "liters": "Fuel volume in liters.",
            "total_amount": "Total amount paid in your selected currency.",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        vehicle_field = self.fields.get("vehicle")
        if vehicle_field is not None:
            queryset = Vehicle.objects.none()
            if user is not None:
                queryset = Vehicle.objects.filter(user=user)
            vehicle_field.queryset = queryset
