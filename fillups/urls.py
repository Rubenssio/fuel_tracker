from django.urls import path

from .views import FillUpCreateView, FillUpDeleteView, FillUpUpdateView

urlpatterns = [
    path("fillups/add", FillUpCreateView.as_view(), name="fillup-add"),
    path("fillups/<int:pk>/edit", FillUpUpdateView.as_view(), name="fillup-edit"),
    path("fillups/<int:pk>/delete", FillUpDeleteView.as_view(), name="fillup-delete"),
]
