from django.urls import path

from .views import (
    VehicleCreateView,
    VehicleDeleteView,
    VehicleListView,
    VehicleUpdateView,
)

urlpatterns = [
    path("vehicles", VehicleListView.as_view(), name="vehicle-list"),
    path("vehicles/add", VehicleCreateView.as_view(), name="vehicle-add"),
    path("vehicles/<int:pk>/edit", VehicleUpdateView.as_view(), name="vehicle-edit"),
    path("vehicles/<int:pk>/delete", VehicleDeleteView.as_view(), name="vehicle-delete"),
]
