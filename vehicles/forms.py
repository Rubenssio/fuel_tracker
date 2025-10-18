from django import forms

from .models import Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["name", "make", "model", "year", "fuel_type"]

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if year is None:
            return year
        if year < 1886 or year > 2100:
            raise forms.ValidationError("Year must be between 1886 and 2100.")
        return year
