"""URL configuration for the bootstrap service."""
from django.urls import path

from core import views

urlpatterns = [
    path("", views.success_view, name="success"),
    path("health", views.health_view, name="health"),
]
