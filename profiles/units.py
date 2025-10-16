"""Utility functions for converting between metric and imperial units."""
from __future__ import annotations

MILES_PER_KM = 0.621371
KM_PER_MILE = 1.60934
GALLONS_PER_LITER = 1 / 3.78541
LITERS_PER_GALLON = 3.78541


def km_to_miles(kilometers: float) -> float:
    """Convert kilometres to miles."""

    return kilometers * MILES_PER_KM


def miles_to_km(miles: float) -> float:
    """Convert miles to kilometres."""

    return miles * KM_PER_MILE


def liters_to_gallons(liters: float) -> float:
    """Convert litres to gallons."""

    return liters * GALLONS_PER_LITER


def gallons_to_liters(gallons: float) -> float:
    """Convert gallons to litres."""

    return gallons * LITERS_PER_GALLON
