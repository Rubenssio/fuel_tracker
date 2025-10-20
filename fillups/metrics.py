"""Utility helpers for computing per-fill and aggregate fuel metrics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, List

from profiles.units import km_to_miles, liters_to_gallons

from .models import FillUp


def _decimal_from_float(value: float) -> Decimal:
    """Return a ``Decimal`` constructed from the string representation of ``value``."""

    return Decimal(str(value))


@dataclass
class PerFill:
    """Represents calculated metrics for a single fill-up entry."""

    fillup: FillUp
    distance_since_last_km: float | None
    unit_price_per_liter: Decimal | None
    efficiency_l_per_100km: float | None
    efficiency_mpg: float | None
    cost_per_km: Decimal | None
    cost_per_mile: Decimal | None


def per_fill_metrics(entries: List[FillUp]) -> list[PerFill]:
    """Compute per-fill metrics for the provided, pre-sorted fill-up entries."""

    results: list[PerFill] = []
    previous: FillUp | None = None

    miles_per_km_decimal = _decimal_from_float(km_to_miles(1.0))
    km_per_mile_decimal = Decimal("1") / miles_per_km_decimal

    for entry in entries:
        distance_km: float | None = None
        unit_price: Decimal | None = None
        efficiency_l_per_100km: float | None = None
        efficiency_mpg: float | None = None
        cost_per_km: Decimal | None = None
        cost_per_mile: Decimal | None = None

        liters = entry.liters
        total_amount = entry.total_amount

        if liters > 0:
            unit_price = total_amount / liters

        if previous is not None:
            raw_distance = entry.odometer_km - previous.odometer_km
            if raw_distance > 0:
                distance_decimal = Decimal(raw_distance)
                distance_km = float(distance_decimal)

                if liters > 0:
                    efficiency_l_per_100km = float((liters * Decimal(100)) / distance_decimal)
                    gallons = liters_to_gallons(float(liters))
                    miles = km_to_miles(distance_km)
                    if gallons > 0:
                        efficiency_mpg = miles / gallons

                if total_amount > 0:
                    cost_per_km = total_amount / distance_decimal
                    cost_per_mile = cost_per_km * km_per_mile_decimal

        results.append(
            PerFill(
                fillup=entry,
                distance_since_last_km=distance_km,
                unit_price_per_liter=unit_price,
                efficiency_l_per_100km=efficiency_l_per_100km,
                efficiency_mpg=efficiency_mpg,
                cost_per_km=cost_per_km,
                cost_per_mile=cost_per_mile,
            )
        )

        previous = entry

    return results


def aggregate_metrics(entries: Iterable[FillUp], window_start: date | None = None) -> dict:
    """Compute aggregate metrics over the provided fill-up entries."""

    if window_start is not None:
        filtered = [entry for entry in entries if entry.date >= window_start]
    else:
        filtered = list(entries)

    if not filtered:
        return {
            "avg_cost_per_liter": None,
            "avg_consumption_l_per_100km": None,
            "avg_consumption_mpg": None,
            "avg_distance_per_day_km": None,
            "avg_cost_per_km": None,
            "avg_cost_per_mile": None,
            "total_spend": Decimal("0"),
            "total_distance_km": 0.0,
        }

    sorted_entries = sorted(filtered, key=lambda entry: (entry.vehicle_id, entry.date, entry.id))

    total_spend = Decimal("0")
    total_liters = Decimal("0")
    total_distance_decimal = Decimal("0")
    liters_for_distance = Decimal("0")
    cost_for_distance = Decimal("0")

    prev_by_vehicle: dict[int, FillUp] = {}
    min_date: date | None = None
    max_date: date | None = None

    for entry in sorted_entries:
        total_spend += entry.total_amount
        total_liters += entry.liters

        if min_date is None or entry.date < min_date:
            min_date = entry.date
        if max_date is None or entry.date > max_date:
            max_date = entry.date

        previous = prev_by_vehicle.get(entry.vehicle_id)
        if previous is not None:
            raw_distance = entry.odometer_km - previous.odometer_km
            if raw_distance > 0:
                distance_decimal = Decimal(raw_distance)
                total_distance_decimal += distance_decimal
                liters_for_distance += entry.liters
                cost_for_distance += entry.total_amount

        prev_by_vehicle[entry.vehicle_id] = entry

    avg_cost_per_liter: Decimal | None = None
    if total_liters > 0:
        avg_cost_per_liter = total_spend / total_liters

    avg_consumption_l_per_100km: float | None = None
    avg_consumption_mpg: float | None = None
    if total_distance_decimal > 0 and liters_for_distance > 0:
        avg_consumption_l_per_100km = float((liters_for_distance * Decimal(100)) / total_distance_decimal)
        gallons = liters_to_gallons(float(liters_for_distance))
        miles = km_to_miles(float(total_distance_decimal))
        if gallons > 0:
            avg_consumption_mpg = miles / gallons

    avg_cost_per_km: Decimal | None = None
    avg_cost_per_mile: Decimal | None = None
    if total_distance_decimal > 0 and cost_for_distance > 0:
        avg_cost_per_km = cost_for_distance / total_distance_decimal
        miles_per_km_decimal = _decimal_from_float(km_to_miles(1.0))
        km_per_mile_decimal = Decimal("1") / miles_per_km_decimal
        avg_cost_per_mile = avg_cost_per_km * km_per_mile_decimal

    avg_distance_per_day_km: float | None = None
    if max_date is not None and min_date is not None:
        if window_start is not None:
            period_start = window_start
            period_end = date.today()
        else:
            period_start = min_date
            period_end = max_date

        if period_end < period_start:
            period_end = period_start

        day_count = max((period_end - period_start).days + 1, 1)
        avg_distance_per_day_km = float(total_distance_decimal / Decimal(day_count))

    return {
        "avg_cost_per_liter": avg_cost_per_liter,
        "avg_consumption_l_per_100km": avg_consumption_l_per_100km,
        "avg_consumption_mpg": avg_consumption_mpg,
        "avg_distance_per_day_km": avg_distance_per_day_km,
        "avg_cost_per_km": avg_cost_per_km,
        "avg_cost_per_mile": avg_cost_per_mile,
        "total_spend": total_spend,
        "total_distance_km": float(total_distance_decimal),
    }
