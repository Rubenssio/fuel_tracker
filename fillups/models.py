from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from . import validators


class FillUp(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fillups",
        editable=False,
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="fillups",
    )
    date = models.DateField()
    odometer_km = models.PositiveIntegerField()
    station_name = models.CharField(max_length=100)
    fuel_brand = models.CharField(max_length=64, blank=True)
    fuel_grade = models.CharField(max_length=64, blank=True)
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "vehicle", "-date"],
                name="ix_fill_user_veh_date",
            ),
            models.Index(
                fields=["user", "-date"],
                name="ix_fill_user_date",
            ),
            models.Index(
                fields=["user", "fuel_brand"],
                name="ix_fill_user_brand",
            ),
            models.Index(
                fields=["user", "fuel_grade"],
                name="ix_fill_user_grade",
            ),
            models.Index(
                fields=["user", "station_name"],
                name="ix_fill_user_station",
            ),
            models.Index(
                fields=["vehicle", "odometer_km"],
                name="ix_fill_vehicle_odo",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                name="chk_liters_positive",
                check=Q(liters__gt=0),
            ),
            models.CheckConstraint(
                name="chk_total_positive",
                check=Q(total_amount__gt=0),
            ),
        ]
        ordering = ["date", "id"]

    def clean(self) -> None:
        super().clean()
        errors: dict[str, list[str]] = {}

        if self.date:
            try:
                validators.validate_not_future_date(self.date)
            except ValidationError as exc:
                errors.setdefault("date", []).extend(exc.messages)

        if self.odometer_km is not None and self.odometer_km <= 0:
            errors.setdefault("odometer_km", []).append(
                "Odometer reading must be greater than 0."
            )

        if self.liters is not None and self.liters <= 0:
            errors.setdefault("liters", []).append(
                "Fuel volume must be greater than 0."
            )

        if self.total_amount is not None and self.total_amount <= 0:
            errors.setdefault("total_amount", []).append(
                "Total amount must be greater than 0."
            )

        if self.vehicle_id and self.date and self.odometer_km is not None:
            prev_entry, next_entry = validators.get_prev_next(
                vehicle=self.vehicle,
                date=self.date,
                pk=self.pk,
            )
            try:
                validators.validate_monotonic(
                    self.odometer_km,
                    prev_entry,
                    next_entry,
                )
            except ValidationError as exc:
                errors.setdefault("odometer_km", []).extend(exc.messages)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.vehicle_id:
            # Keep the user field aligned with the related vehicle owner.
            self.user_id = self.vehicle.user_id
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Fill-up on {self.date} at {self.odometer_km} km"
