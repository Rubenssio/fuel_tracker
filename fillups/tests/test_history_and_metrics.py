from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from fillups.models import FillUp
from profiles.models import Profile
from vehicles.models import Vehicle


class HistoryAndMetricsViewTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="demo", email="demo@example.com", password="password123"
        )
        self.client = Client()
        assert self.client.login(username="demo", password="password123")

        self.vehicle = Vehicle.objects.create(user=self.user, name="Test Car")

        Profile.objects.create(
            user=self.user,
            currency="USD",
            distance_unit=Profile.UNIT_KILOMETERS,
            volume_unit=Profile.UNIT_LITERS,
            timezone="UTC",
            utc_offset_minutes=0,
        )

        first_date = date.today() - timedelta(days=10)
        second_date = date.today() - timedelta(days=5)

        FillUp.objects.create(
            vehicle=self.vehicle,
            date=first_date,
            odometer_km=1000,
            station_name="Station A",
            fuel_brand="Brand",
            fuel_grade="Regular",
            liters=Decimal("40.00"),
            total_amount=Decimal("80.00"),
        )
        FillUp.objects.create(
            vehicle=self.vehicle,
            date=second_date,
            odometer_km=1200,
            station_name="Station B",
            fuel_brand="Brand",
            fuel_grade="Premium",
            liters=Decimal("45.00"),
            total_amount=Decimal("99.00"),
        )

    def test_history_and_metrics_render_in_metric(self) -> None:
        history_response = self.client.get(reverse("history-list"))
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, "L/100km")
        self.assertContains(history_response, "/ km")

        metrics_response = self.client.get(reverse("metrics"))
        self.assertEqual(metrics_response.status_code, 200)
        self.assertContains(metrics_response, "All-time")
        self.assertContains(metrics_response, "USD")

    def test_switching_to_imperial_units(self) -> None:
        profile = Profile.objects.get(user=self.user)
        profile.distance_unit = Profile.UNIT_MILES
        profile.volume_unit = Profile.UNIT_GALLONS
        profile.currency = "USD"
        profile.save()

        history_response = self.client.get(reverse("history-list"))
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, "MPG")
        self.assertContains(history_response, "/ mi")

        metrics_response = self.client.get(reverse("metrics"))
        self.assertEqual(metrics_response.status_code, 200)
        self.assertContains(metrics_response, "MPG")
        self.assertContains(metrics_response, "/ mi")


class BaselineFillUpDisplayTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="baseline", email="baseline@example.com", password="password123"
        )
        self.client = Client()
        assert self.client.login(username="baseline", password="password123")

        self.vehicle = Vehicle.objects.create(user=self.user, name="Solo Car")

        Profile.objects.create(
            user=self.user,
            currency="USD",
            distance_unit=Profile.UNIT_KILOMETERS,
            volume_unit=Profile.UNIT_LITERS,
            timezone="UTC",
            utc_offset_minutes=0,
        )

        FillUp.objects.create(
            vehicle=self.vehicle,
            date=date.today(),
            odometer_km=1000,
            station_name="Solo Station",
            fuel_brand="Brand",
            fuel_grade="Regular",
            liters=Decimal("40.00"),
            total_amount=Decimal("80.00"),
        )

    def test_history_displays_unit_price_for_baseline_fillup(self) -> None:
        response = self.client.get(reverse("history-list"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        self.assertIn("USD 2.00 / L", html)
        self.assertGreaterEqual(html.count("<td>—</td>"), 3)

    def test_statistics_cost_series_includes_baseline(self) -> None:
        response = self.client.get(reverse("statistics"))
        self.assertEqual(response.status_code, 200)

        chart_cost = response.context["chart_cost"]
        self.assertTrue(chart_cost["has_data"])
        self.assertGreaterEqual(len(chart_cost["points"]), 1)
