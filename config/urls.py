"""URL configuration for the bootstrap service."""
from django.urls import include, path

from core import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("health", views.health_view, name="health"),
    path("", include("accounts.urls")),
    path("", include("profiles.urls")),
    path("", include("vehicles.urls")),
]
