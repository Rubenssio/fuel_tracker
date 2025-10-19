"""Helper utilities for statistics views and templates."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from .models import FillUp


def window_start_from_param(param: str, today: date) -> date | None:
    """Return the inclusive start date for the requested statistics window."""

    normalized = (param or "").strip().lower()
    if normalized == "90":
        return today - timedelta(days=90)
    if normalized == "ytd":
        return date(today.year, 1, 1)
    # Default to 30 days.
    return today - timedelta(days=30)


def timeseries_cost_per_liter(entries: Iterable[FillUp]) -> list[tuple[date, Decimal]]:
    """Return a chronological series of per-fill cost per liter values."""

    series: list[tuple[date, Decimal]] = []
    for entry in sorted(entries, key=lambda item: (item.date, item.id)):
        liters = entry.liters
        if liters is None or liters <= 0:
            continue
        price = entry.total_amount / liters
        series.append((entry.date, price))
    return series


def timeseries_consumption(entries: Iterable[FillUp]) -> list[tuple[date, float | None]]:
    """Return a chronological series of per-fill consumption values in L/100km."""

    entries_list = list(entries)
    if not entries_list:
        return []

    consumption_by_id: dict[int, float | None] = {}
    previous_by_vehicle: dict[int, FillUp] = {}

    for entry in sorted(entries_list, key=lambda item: (item.vehicle_id, item.date, item.id)):
        previous = previous_by_vehicle.get(entry.vehicle_id)
        value: float | None = None
        if previous is not None:
            distance = entry.odometer_km - previous.odometer_km
            if distance > 0 and entry.liters > 0:
                value = float((entry.liters * Decimal(100)) / Decimal(distance))
        consumption_by_id[entry.id] = value
        previous_by_vehicle[entry.vehicle_id] = entry

    ordered = sorted(entries_list, key=lambda item: (item.date, item.id))
    return [(entry.date, consumption_by_id.get(entry.id)) for entry in ordered]


def brand_grade_summary(entries: Iterable[FillUp]) -> list[dict]:
    """Compute average cost per liter and consumption grouped by brand/grade."""

    entries_list = list(entries)
    if not entries_list:
        return []

    group_totals: dict[tuple[str, str], dict] = {}
    previous_by_vehicle: dict[int, FillUp] = {}

    for entry in sorted(entries_list, key=lambda item: (item.vehicle_id, item.date, item.id)):
        key = (entry.fuel_brand or "", entry.fuel_grade or "")
        data = group_totals.setdefault(
            key,
            {
                "brand": key[0],
                "grade": key[1],
                "total_amount": Decimal("0"),
                "total_liters": Decimal("0"),
                "consumptions": [],
                "count": 0,
            },
        )

        liters = entry.liters
        if liters is not None and liters > 0:
            data["total_amount"] += entry.total_amount
            data["total_liters"] += liters

        previous = previous_by_vehicle.get(entry.vehicle_id)
        if previous is not None:
            distance = entry.odometer_km - previous.odometer_km
            if distance > 0 and liters is not None and liters > 0:
                consumption = float((liters * Decimal(100)) / Decimal(distance))
                data["consumptions"].append(consumption)

        data["count"] += 1
        previous_by_vehicle[entry.vehicle_id] = entry

    results: list[dict] = []
    for data in group_totals.values():
        avg_cost: Decimal | None = None
        if data["total_liters"] > 0:
            avg_cost = data["total_amount"] / data["total_liters"]

        avg_consumption: float | None = None
        if data["consumptions"]:
            avg_consumption = sum(data["consumptions"]) / len(data["consumptions"])

        results.append(
            {
                "brand": data["brand"],
                "grade": data["grade"],
                "avg_cost_per_liter": avg_cost,
                "avg_consumption_l_per_100km": avg_consumption,
                "count": data["count"],
            }
        )

    results.sort(key=lambda item: (item["brand"].lower(), item["grade"].lower()))
    return results


def to_svg_path(points: list[tuple[float, float]]) -> str:
    """Convert a list of 2D points into an SVG path string."""

    if not points:
        return ""
    commands = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for x, y in points[1:]:
        commands.append(f"L {x:.2f} {y:.2f}")
    return " ".join(commands)
