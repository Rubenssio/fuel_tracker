"""Views for managing user profile settings."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import ProfileForm
from .models import Profile
from . import units


class SettingsView(LoginRequiredMixin, View):
    """Display and update the authenticated user's profile."""

    template_name = "profiles/settings.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        profile = self._get_profile(request)
        form = ProfileForm(instance=profile)
        preview = self._build_preview(profile)
        return render(request, self.template_name, {"form": form, "preview": preview})

    def post(self, request: HttpRequest) -> HttpResponse:
        profile = self._get_profile(request)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated.")
            return redirect(reverse("profiles:settings"))
        preview = self._build_preview(profile)
        return render(request, self.template_name, {"form": form, "preview": preview})

    def _get_profile(self, request: HttpRequest) -> Profile:
        profile, _created = Profile.objects.get_or_create(user=request.user)
        return profile

    def _build_preview(self, profile: Profile) -> dict[str, str]:
        sample_distance_km = 100.0
        sample_volume_l = 50.0
        sample_currency_amount = 42.50

        if profile.distance_unit == Profile.UNIT_MILES:
            distance_value = units.km_to_miles(sample_distance_km)
            distance_label = f"~{distance_value:.1f} mi"
        else:
            distance_label = f"{sample_distance_km:.0f} km"

        if profile.volume_unit == Profile.UNIT_GALLONS:
            volume_value = units.liters_to_gallons(sample_volume_l)
            volume_label = f"~{volume_value:.1f} gal"
        else:
            volume_label = f"{sample_volume_l:.0f} L"

        currency_label = f"{profile.currency} {sample_currency_amount:,.2f}"

        return {
            "distance": distance_label,
            "volume": volume_label,
            "currency": currency_label,
        }
