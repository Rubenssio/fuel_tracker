from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from fillups.models import FillUp
from vehicles.models import Vehicle

from fillups.stats import (
    brand_grade_summary,
    timeseries_consumption,
    timeseries_cost_per_liter,
    to_svg_path,
    window_start_from_param,
)


class StatisticsHelpersTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="stats", email="stats@example.com", password="password123"
        )
        self.vehicle = Vehicle.objects.create(user=self.user, name="Stats Car")

        base_date = date.today() - timedelta(days=3)
        self.fill1 = FillUp.objects.create(
            vehicle=self.vehicle,
            date=base_date,
            odometer_km=1000,
            station_name="Station A",
            fuel_brand="BrandA",
            fuel_grade="Regular",
            liters=Decimal("40.00"),
            total_amount=Decimal("80.00"),
        )
        self.fill2 = FillUp.objects.create(
            vehicle=self.vehicle,
            date=base_date + timedelta(days=1),
            odometer_km=1200,
            station_name="Station B",
            fuel_brand="BrandA",
            fuel_grade="Regular",
            liters=Decimal("50.00"),
            total_amount=Decimal("100.00"),
        )
        self.fill3 = FillUp.objects.create(
            vehicle=self.vehicle,
            date=base_date + timedelta(days=2),
            odometer_km=1400,
            station_name="Station C",
            fuel_brand="BrandB",
            fuel_grade="Premium",
            liters=Decimal("45.00"),
            total_amount=Decimal("90.00"),
        )

    def test_window_start_from_param(self) -> None:
        today = date(2025, 1, 15)
        self.assertEqual(window_start_from_param("30", today), date(2024, 12, 16))
        self.assertEqual(window_start_from_param("90", today), date(2024, 10, 17))
        self.assertEqual(window_start_from_param("ytd", today), date(2025, 1, 1))
        self.assertEqual(window_start_from_param("unknown", today), date(2024, 12, 16))

    def test_timeseries_cost_per_liter(self) -> None:
        series = timeseries_cost_per_liter([self.fill2, self.fill1, self.fill3])
        self.assertEqual([item[0] for item in series], [self.fill1.date, self.fill2.date, self.fill3.date])
        prices = [item[1] for item in series]
        self.assertEqual(prices[0], Decimal("2"))
        self.assertEqual(prices[1], Decimal("2"))
        self.assertEqual(prices[2], Decimal("2"))

    def test_timeseries_consumption(self) -> None:
        series = timeseries_consumption([self.fill1, self.fill2, self.fill3])
        self.assertEqual(series[0][0], self.fill1.date)
        self.assertIsNone(series[0][1])
        self.assertAlmostEqual(series[1][1], 25.0)
        self.assertAlmostEqual(series[2][1], 22.5)

    def test_brand_grade_summary(self) -> None:
        summary = brand_grade_summary([self.fill1, self.fill2, self.fill3])
        self.assertEqual(len(summary), 2)

        brand_a = next(item for item in summary if item["brand"] == "BrandA")
        brand_b = next(item for item in summary if item["brand"] == "BrandB")

        self.assertEqual(brand_a["count"], 2)
        self.assertEqual(brand_a["avg_cost_per_liter"], Decimal("2"))
        self.assertAlmostEqual(brand_a["avg_consumption_l_per_100km"], 25.0)

        self.assertEqual(brand_b["count"], 1)
        self.assertEqual(brand_b["avg_cost_per_liter"], Decimal("2"))
        self.assertAlmostEqual(brand_b["avg_consumption_l_per_100km"], 22.5)

    def test_to_svg_path(self) -> None:
        path = to_svg_path([(0, 10), (50, 20), (100, 5)])
        self.assertEqual(path, "M 0.00 10.00 L 50.00 20.00 L 100.00 5.00")
