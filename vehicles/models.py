from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    name = models.CharField(max_length=64)
    make = models.CharField(max_length=64, blank=True)
    model = models.CharField(max_length=64, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    fuel_type = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="uniq_user_vehicle_name",
            )
        ]
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name
