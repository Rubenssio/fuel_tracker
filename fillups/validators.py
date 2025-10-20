from __future__ import annotations

from typing import Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone


def get_prev_next(vehicle, date, pk: Optional[int] = None) -> Tuple[Optional["FillUp"], Optional["FillUp"]]:
    from .models import FillUp

    current_pk = pk if pk is not None else 2**63 - 1

    queryset = FillUp.objects.filter(vehicle=vehicle)

    previous = (
        queryset.filter(
            Q(date__lt=date)
            | (Q(date=date) & Q(pk__lt=current_pk))
        )
        .order_by("-date", "-pk")
        .first()
    )

    next_ = (
        queryset.filter(
            Q(date__gt=date)
            | (Q(date=date) & Q(pk__gt=(pk if pk is not None else current_pk)))
        )
        .order_by("date", "pk")
        .first()
    )

    return previous, next_


def validate_monotonic(odometer_km: int, prev, next_) -> None:
    errors = []
    if prev and odometer_km <= prev.odometer_km:
        errors.append("Odometer reading must be greater than the previous fill-up.")
    if next_ and odometer_km >= next_.odometer_km:
        errors.append("Odometer reading must be less than the next fill-up.")
    if errors:
        raise ValidationError(errors)


def validate_not_future_date(date) -> None:
    today = timezone.localdate()
    if date > today:
        raise ValidationError("Date cannot be in the future.")
