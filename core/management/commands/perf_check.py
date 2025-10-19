"""Management command for lightweight local performance checks."""
from __future__ import annotations

import time
from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from fillups.metrics import aggregate_metrics
from fillups.models import FillUp
from fillups.stats import (
    brand_grade_summary,
    timeseries_consumption,
    timeseries_cost_per_liter,
)


class Command(BaseCommand):
    help = "Run lightweight timing checks for History and Statistics views."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of the demo user")
        parser.add_argument(
            "--vehicle",
            default="all",
            help="Vehicle ID to scope queries to, or 'all' for every vehicle (default)",
        )

    def handle(self, *args, **options):
        email: str = options["email"].strip().lower()
        vehicle_option: str = str(options["vehicle"]).strip().lower()

        if not email:
            raise CommandError("--email is required")

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:  # pragma: no cover - defensive
            raise CommandError(f"No user found for email {email!r}") from exc

        filters = {"user": user}
        vehicle_label = "all"
        if vehicle_option != "all":
            try:
                vehicle_id = int(vehicle_option)
            except (TypeError, ValueError) as exc:
                raise CommandError("--vehicle must be an integer or 'all'") from exc
            if not user.vehicles.filter(id=vehicle_id).exists():
                raise CommandError(
                    f"User {email} does not own a vehicle with id={vehicle_id}"
                )
            filters["vehicle_id"] = vehicle_id
            vehicle_label = str(vehicle_id)

        history_qs = (
            FillUp.objects.filter(**filters)
            .select_related("vehicle")
            .order_by("-date", "-id")
        )
        start = time.monotonic()
        history_rows = list(history_qs[:50])
        history_elapsed = (time.monotonic() - start) * 1000

        stats_qs = (
            FillUp.objects.filter(**filters)
            .select_related("vehicle")
            .order_by("vehicle_id", "date", "id")
        )
        start = time.monotonic()
        stats_rows = list(stats_qs)
        stats_elapsed = (time.monotonic() - start) * 1000

        start = time.monotonic()
        self._run_statistics_helpers(stats_rows)
        helper_elapsed = (time.monotonic() - start) * 1000

        self.stdout.write(
            self.style.MIGRATE_HEADING("Performance check results"),
        )
        self.stdout.write(f"User: {email}")
        self.stdout.write(f"Vehicle scope: {vehicle_label}")
        self.stdout.write(
            f"History query: fetched {len(history_rows)} rows in {history_elapsed:.1f} ms",
        )
        self.stdout.write(
            f"Statistics query: fetched {len(stats_rows)} rows in {stats_elapsed:.1f} ms",
        )
        self.stdout.write(
            f"Statistics helpers (aggregates & series): {helper_elapsed:.1f} ms",
        )

    def _run_statistics_helpers(self, entries: Iterable[FillUp]) -> None:
        entries_list = list(entries)
        aggregate_metrics(entries_list)
        brand_grade_summary(entries_list)
        timeseries_cost_per_liter(entries_list)
        timeseries_consumption(entries_list)
