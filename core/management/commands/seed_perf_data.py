"""Management command to seed high-volume demo data for perf checks."""
from __future__ import annotations

import random
import secrets
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fillups.models import FillUp
from vehicles.models import Vehicle


BRANDS = [
    "FuelOne",
    "EcoFuel",
    "SpeedyGas",
    "MetroFuel",
]

GRADES = [
    "Regular",
    "Midgrade",
    "Premium",
]

STATIONS = [
    "Downtown Plaza",
    "Suburb Central",
    "Highway Stop",
    "Airport Station",
]


class Command(BaseCommand):
    help = "Seed a demo account with vehicles and fill-ups for local perf testing."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of the demo user")
        parser.add_argument(
            "--vehicles",
            type=int,
            default=2,
            help="Number of vehicles to generate (default: 2)",
        )
        parser.add_argument(
            "--fillups",
            type=int,
            default=5000,
            help="Total number of fill-ups to generate (default: 5000)",
        )

    def handle(self, *args, **options):
        email: str = options["email"].strip().lower()
        vehicle_count: int = int(options["vehicles"])
        fillup_count: int = int(options["fillups"])

        if not email:
            raise CommandError("--email is required")
        if vehicle_count <= 0:
            raise CommandError("--vehicles must be greater than 0")
        if fillup_count <= 0:
            raise CommandError("--fillups must be greater than 0")

        User = get_user_model()
        password = secrets.token_urlsafe(12)

        rng = random.Random()

        with transaction.atomic():
            user, _created = User.objects.get_or_create(
                email=email,
                defaults={"first_name": "Demo", "last_name": "Driver"},
            )
            user.first_name = user.first_name or "Demo"
            user.last_name = user.last_name or "Driver"
            user.is_active = True
            user.set_password(password)
            user.save(update_fields=["first_name", "last_name", "is_active", "password"])

            # Clean up any prior data for repeatability.
            FillUp.objects.filter(user=user).delete()
            Vehicle.objects.filter(user=user).delete()

            vehicles: list[Vehicle] = []
            for index in range(vehicle_count):
                vehicle = Vehicle.objects.create(
                    user=user,
                    name=f"Demo Vehicle {index + 1}",
                    make=rng.choice(["Acme", "Contoso", "Initech", "Vandelay"]),
                    model=rng.choice(["Explorer", "Ranger", "Cruiser", "CityRide"]),
                    year=rng.randint(date.today().year - 8, date.today().year),
                    fuel_type=rng.choice(["Gasoline", "Diesel"]),
                )
                vehicles.append(vehicle)

            if not vehicles:
                raise CommandError("No vehicles created; cannot seed fill-ups")

            base_start = date.today() - timedelta(days=540)
            total_created = 0
            fillups_per_vehicle = [fillup_count // len(vehicles)] * len(vehicles)
            for idx in range(fillup_count % len(vehicles)):
                fillups_per_vehicle[idx] += 1

            for vehicle, target_count in zip(vehicles, fillups_per_vehicle):
                if target_count <= 0:
                    continue
                current_date = base_start + timedelta(days=rng.randint(0, 10))
                current_odometer = rng.randint(10_000, 40_000)

                for _ in range(target_count):
                    # Spread fill-ups every 3-7 days.
                    current_date += timedelta(days=rng.randint(3, 7))
                    if current_date > date.today():
                        current_date = date.today()

                    distance = rng.randint(250, 550)
                    current_odometer += distance

                    liters_value = Decimal(rng.uniform(30.0, 65.0)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    price_per_liter = Decimal(rng.uniform(1.0, 2.0)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    total_amount = (liters_value * price_per_liter).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                    fillup = FillUp(
                        vehicle=vehicle,
                        date=current_date,
                        odometer_km=current_odometer,
                        station_name=rng.choice(STATIONS),
                        fuel_brand=rng.choice(BRANDS),
                        fuel_grade=rng.choice(GRADES),
                        liters=liters_value,
                        total_amount=total_amount,
                        notes="Perf seed auto-generated.",
                    )
                    fillup.save()
                    total_created += 1

            self.stdout.write(self.style.SUCCESS("Perf seed complete."))
            self.stdout.write(
                f"User: {email}\nPassword: {password}\n"
                f"Vehicles created: {len(vehicles)}\nFill-ups created: {total_created}"
            )
