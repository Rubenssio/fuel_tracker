"""URL routing for profile settings."""
from __future__ import annotations

from django.urls import path

from .views import SettingsView

app_name = "profiles"

urlpatterns = [
    path("settings", SettingsView.as_view(), name="settings"),
]
