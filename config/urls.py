"""URL configuration for the bootstrap service."""
from django.urls import include, path
from django.views.generic import TemplateView

from core import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("health", views.health_view, name="health"),
    path(
        "legal/terms",
        TemplateView.as_view(template_name="legal/terms.html"),
        name="legal-terms",
    ),
    path(
        "legal/privacy",
        TemplateView.as_view(template_name="legal/privacy.html"),
        name="legal-privacy",
    ),
    path("", include("accounts.urls")),
    path("", include("profiles.urls")),
    path("", include("vehicles.urls")),
    path("", include("fillups.urls")),
]

handler400 = "config.views.error_400"
handler403 = "config.views.error_403"
handler404 = "config.views.error_404"
handler500 = "config.views.error_500"
