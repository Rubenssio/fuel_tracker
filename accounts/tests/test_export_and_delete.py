from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from fillups.models import FillUp
from vehicles.models import Vehicle


User = get_user_model()


class AccountExportAndDeleteTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@example.com",
            password="test-pass",
        )
        self.vehicle = Vehicle.objects.create(
            user=self.user,
            name="Daily Driver",
            make="Make",
            model="Model",
            year=2020,
            fuel_type="Gasoline",
        )
        self.first_fill = FillUp.objects.create(
            vehicle=self.vehicle,
            date=date(2024, 1, 1),
            odometer_km=1000,
            station_name="Station One",
            fuel_brand="BrandA",
            fuel_grade="Premium",
            liters=Decimal("40.00"),
            total_amount=Decimal("80.00"),
            notes="Initial fill",
        )
        self.second_fill = FillUp.objects.create(
            vehicle=self.vehicle,
            date=date(2024, 1, 15),
            odometer_km=1100,
            station_name="Station Two",
            fuel_brand="BrandB",
            fuel_grade="Regular",
            liters=Decimal("8.00"),
            total_amount=Decimal("16.00"),
            notes="Top up",
        )

    def test_export_returns_zip_with_csvs(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:export"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")

        archive = zipfile.ZipFile(io.BytesIO(response.content))
        names = set(archive.namelist())
        self.assertIn("vehicles.csv", names)
        self.assertIn("fillups.csv", names)

        vehicles_csv = archive.read("vehicles.csv").decode("utf-8")
        fillups_csv = archive.read("fillups.csv").decode("utf-8")

        vehicle_rows = list(csv.reader(io.StringIO(vehicles_csv)))
        self.assertEqual(vehicle_rows[0], ["id", "name", "make", "model", "year", "fuel_type", "created_at", "updated_at"])
        self.assertEqual(vehicle_rows[1][0], str(self.vehicle.id))
        self.assertEqual(vehicle_rows[1][1], "Daily Driver")

        fillup_rows = list(csv.reader(io.StringIO(fillups_csv)))
        self.assertEqual(
            fillup_rows[0],
            [
                "id",
                "vehicle_id",
                "date",
                "odometer_km",
                "station",
                "fuel_brand",
                "fuel_grade",
                "liters",
                "total_currency_amount",
                "currency",
                "notes",
                "created_at",
                "updated_at",
                "unit_price_per_liter",
                "distance_since_last_km",
                "consumption_l_per_100km",
                "cost_per_km",
            ],
        )
        # Last fill-up should include derived metrics.
        latest = fillup_rows[-1]
        self.assertEqual(latest[1], str(self.vehicle.id))
        self.assertEqual(latest[7], "8.00")
        self.assertEqual(latest[8], "16.00")
        self.assertEqual(latest[9], "USD")
        self.assertEqual(latest[13], "2.00")
        self.assertEqual(latest[14], "100")
        self.assertEqual(latest[15], "8.0")
        self.assertEqual(latest[16], "0.16")

    def test_delete_account_removes_related_data(self) -> None:
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:delete"), {"confirm": "DELETE"})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Vehicle.objects.filter(pk=self.vehicle.pk).exists())
        self.assertFalse(FillUp.objects.filter(pk=self.first_fill.pk).exists())
        self.assertFalse(FillUp.objects.filter(pk=self.second_fill.pk).exists())
