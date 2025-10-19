"""Utility helpers for computing per-fill and aggregate fuel metrics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

from profiles.models import Profile
from profiles.units import LITERS_PER_GALLON, km_to_miles, liters_to_gallons


@dataclass
class PerFill:
    """Represents calculated metrics for a single fill-up entry."""

    fillup: object
    distance_since_last_km: float | None
    unit_price_per_liter: float | None
    efficiency_l_per_100km: float | None
    efficiency_mpg: float | None
    cost_per_km: float | None
    cost_per_mile: float | None


def per_fill_metrics(entries_for_vehicle_sorted: Sequence[object]) -> list[PerFill]:
    """Compute per-fill metrics for a list of entries belonging to one vehicle.

    The ``entries_for_vehicle_sorted`` sequence must already be sorted in
    chronological order by ``(date, id)`` for a single vehicle. The first entry
    is treated as the baseline and therefore has no calculated values.
    """

    results: list[PerFill] = []
    prev = None

    for entry in entries_for_vehicle_sorted:
        distance_km: float | None = None
        unit_price: float | None = None
        efficiency_l_per_100km: float | None = None
        efficiency_mpg: float | None = None
        cost_per_km: float | None = None
        cost_per_mile: float | None = None

        if prev is not None:
            raw_distance = entry.odometer_km - prev.odometer_km
            if raw_distance > 0:
                distance_km = float(raw_distance)

                liters = float(entry.liters)
                if liters > 0:
                    unit_price = float(entry.total_amount) / liters

                if liters > 0 and distance_km > 0:
                    efficiency_l_per_100km = (liters * 100) / distance_km
                    gallons = liters_to_gallons(liters)
                    miles = km_to_miles(distance_km)
                    if gallons > 0:
                        efficiency_mpg = miles / gallons

                    if distance_km > 0:
                        cost_per_km = float(entry.total_amount) / distance_km
                        miles_distance = km_to_miles(distance_km)
                        if miles_distance > 0:
                            cost_per_mile = float(entry.total_amount) / miles_distance

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

        prev = entry

    return results


def aggregate_metrics(
    entries: Iterable[object], *, window_start: date | None = None
) -> dict[str, float | None]:
    """Compute aggregate metrics for the provided entries.

    The ``entries`` iterable should already be limited to entries belonging to a
    single user (all vehicles or one vehicle). The results are returned in
    canonical units (kilometres and litres) without any rounding suitable for
    display.
    """

    entries_list = list(entries)
    if window_start is not None:
        entries_list = [entry for entry in entries_list if entry.date >= window_start]

    if not entries_list:
        return {
            "avg_cost_per_liter": None,
            "avg_consumption_l_per_100km": None,
            "avg_consumption_mpg": None,
            "avg_distance_per_day_km": None,
            "avg_cost_per_km": None,
            "avg_cost_per_mile": None,
            "total_spend": 0.0,
            "total_distance_km": 0.0,
            "total_liters": 0.0,
        }

    sorted_entries = sorted(entries_list, key=lambda entry: (entry.vehicle_id, entry.date, entry.id))

    total_spend = 0.0
    total_liters = 0.0
    total_distance_km = 0.0
    liters_for_distance = 0.0
    cost_for_distance = 0.0

    prev_by_vehicle: dict[int, object] = {}
    min_date: date | None = None
    max_date: date | None = None

    for entry in sorted_entries:
        total_spend += float(entry.total_amount)
        liters = float(entry.liters)
        total_liters += liters

        if min_date is None or entry.date < min_date:
            min_date = entry.date
        if max_date is None or entry.date > max_date:
            max_date = entry.date

        prev = prev_by_vehicle.get(entry.vehicle_id)
        if prev is not None:
            raw_distance = entry.odometer_km - prev.odometer_km
            if raw_distance > 0:
                distance_km = float(raw_distance)
                total_distance_km += distance_km
                liters_for_distance += liters
                cost_for_distance += float(entry.total_amount)

        prev_by_vehicle[entry.vehicle_id] = entry

    avg_cost_per_liter = None
    if total_liters > 0:
        avg_cost_per_liter = total_spend / total_liters

    avg_consumption_l_per_100km = None
    avg_consumption_mpg = None
    if total_distance_km > 0 and liters_for_distance > 0:
        avg_consumption_l_per_100km = (liters_for_distance * 100) / total_distance_km
        gallons = liters_to_gallons(liters_for_distance)
        miles = km_to_miles(total_distance_km)
        if gallons > 0:
            avg_consumption_mpg = miles / gallons

    avg_cost_per_km = None
    avg_cost_per_mile = None
    if total_distance_km > 0 and cost_for_distance > 0:
        avg_cost_per_km = cost_for_distance / total_distance_km
        miles = km_to_miles(total_distance_km)
        if miles > 0:
            avg_cost_per_mile = cost_for_distance / miles

    avg_distance_per_day_km = None
    if max_date is not None:
        if window_start is not None:
            period_start = window_start
            period_end = date.today()
        else:
            period_start = min_date or max_date
            period_end = max_date

        if period_start is not None and period_end is not None:
            if period_end < period_start:
                period_end = period_start
            day_count = max((period_end - period_start).days + 1, 1)
            avg_distance_per_day_km = total_distance_km / day_count

    return {
        "avg_cost_per_liter": avg_cost_per_liter,
        "avg_consumption_l_per_100km": avg_consumption_l_per_100km,
        "avg_consumption_mpg": avg_consumption_mpg,
        "avg_distance_per_day_km": avg_distance_per_day_km,
        "avg_cost_per_km": avg_cost_per_km,
        "avg_cost_per_mile": avg_cost_per_mile,
        "total_spend": total_spend,
        "total_distance_km": total_distance_km,
        "total_liters": total_liters,
    }
def round_for_display(values: dict[str, float | None], prefs: Profile) -> dict[str, str | None]:
    """Convert canonical-unit values into rounded display strings."""

    distance_unit = getattr(prefs, "distance_unit", Profile.UNIT_KILOMETERS)
    volume_unit = getattr(prefs, "volume_unit", Profile.UNIT_LITERS)
    currency = getattr(prefs, "currency", "USD")

    result: dict[str, str | None] = {}

    distance_value = values.get("distance_since_last_km")
    if distance_value is not None:
        if distance_unit == Profile.UNIT_MILES:
            distance_value = km_to_miles(distance_value)
        result["distance_since_last"] = f"{int(round(distance_value))} {distance_unit}"
    elif "distance_since_last_km" in values:
        result["distance_since_last"] = None

    unit_price_value = values.get("unit_price_per_liter")
    if unit_price_value is not None:
        if volume_unit == Profile.UNIT_GALLONS:
            unit_price_value *= LITERS_PER_GALLON
        result["unit_price"] = f"{currency} {unit_price_value:.2f}/{volume_unit}"
    elif "unit_price_per_liter" in values:
        result["unit_price"] = None

    efficiency_value = None
    efficiency_unit = None
    if distance_unit == Profile.UNIT_MILES:
        efficiency_value = values.get("efficiency_mpg") or values.get("avg_consumption_mpg")
        efficiency_unit = "MPG"
    else:
        efficiency_value = values.get("efficiency_l_per_100km") or values.get(
            "avg_consumption_l_per_100km"
        )
        efficiency_unit = "L/100km"

    if efficiency_value is not None:
        result_key = "efficiency" if "efficiency_l_per_100km" in values or "efficiency_mpg" in values else "avg_consumption"
        result[result_key] = f"{efficiency_value:.1f} {efficiency_unit}"
    elif any(
        key in values
        for key in ("efficiency_l_per_100km", "efficiency_mpg", "avg_consumption_l_per_100km", "avg_consumption_mpg")
    ):
        result_key = "efficiency" if "efficiency_l_per_100km" in values or "efficiency_mpg" in values else "avg_consumption"
        result[result_key] = None

    cost_per_distance = None
    if distance_unit == Profile.UNIT_MILES:
        cost_per_distance = values.get("cost_per_mile") or values.get("avg_cost_per_mile")
        distance_suffix = "mi"
    else:
        cost_per_distance = values.get("cost_per_km") or values.get("avg_cost_per_km")
        distance_suffix = "km"

    if cost_per_distance is not None:
        result_key = "cost_per_distance" if "cost_per_km" in values or "cost_per_mile" in values else "avg_cost_per_distance"
        result[result_key] = f"{currency} {cost_per_distance:.2f}/{distance_suffix}"
    elif any(key in values for key in ("cost_per_km", "cost_per_mile", "avg_cost_per_km", "avg_cost_per_mile")):
        result_key = "cost_per_distance" if "cost_per_km" in values or "cost_per_mile" in values else "avg_cost_per_distance"
        result[result_key] = None

    avg_cost_per_liter = values.get("avg_cost_per_liter")
    if avg_cost_per_liter is not None:
        if volume_unit == Profile.UNIT_GALLONS:
            avg_cost_per_liter *= LITERS_PER_GALLON
        result["avg_cost_per_volume"] = f"{currency} {avg_cost_per_liter:.2f}/{volume_unit}"
    elif "avg_cost_per_liter" in values:
        result["avg_cost_per_volume"] = None

    avg_distance_per_day = values.get("avg_distance_per_day_km")
    if avg_distance_per_day is not None:
        if distance_unit == Profile.UNIT_MILES:
            avg_distance_per_day = km_to_miles(avg_distance_per_day)
        result["avg_distance_per_day"] = f"{int(round(avg_distance_per_day))} {distance_unit}/day"
    elif "avg_distance_per_day_km" in values:
        result["avg_distance_per_day"] = None

    total_distance = values.get("total_distance_km")
    if total_distance is not None:
        if distance_unit == Profile.UNIT_MILES:
            total_distance = km_to_miles(total_distance)
        result["total_distance"] = f"{int(round(total_distance))} {distance_unit}"
    elif "total_distance_km" in values:
        result["total_distance"] = None

    total_spend = values.get("total_spend")
    if total_spend is not None:
        result["total_spend"] = f"{currency} {total_spend:.2f}"
    elif "total_spend" in values:
        result["total_spend"] = None

    total_liters = values.get("total_liters")
    if total_liters is not None:
        if volume_unit == Profile.UNIT_GALLONS:
            total_liters = liters_to_gallons(total_liters)
        result["total_volume"] = f"{total_liters:.2f} {volume_unit}"
    elif "total_liters" in values:
        result["total_volume"] = None

    return result
