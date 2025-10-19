from __future__ import annotations

import csv
import io
import zipfile
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_http_methods

from audit.models import AuthEvent
from core.logging import cv_correlation_id
from .forms import EmailAuthenticationForm, SignupForm
from fillups.models import FillUp


class SignupView(View):
    template_name = "accounts/signup.html"
    form_class = SignupForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            AuthEvent.objects.create(
                event_type=AuthEvent.EventType.SIGNUP,
                user=user,
                email=user.email or "",
                ip_address=_get_client_ip(request),
                user_agent=_get_user_agent(request),
                correlation_id=_get_correlation_id(request),
            )
            return redirect("/")
        return render(request, self.template_name, {"form": form})


class SigninView(LoginView):
    template_name = "accounts/signin.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)


class SignoutView(LogoutView):
    next_page = "/"


def _get_client_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        for value in forwarded.split(","):
            candidate = value.strip()
            if candidate:
                return candidate
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request: HttpRequest) -> str:
    return request.META.get("HTTP_USER_AGENT", "")


def _get_correlation_id(request: HttpRequest) -> str:
    correlation_id = getattr(request, "correlation_id", None)
    if correlation_id:
        return str(correlation_id)
    context_value = cv_correlation_id.get(None)
    if context_value:
        return str(context_value)
    return ""


def _format_decimal(value: Decimal | None, fmt: str) -> str:
    if value is None:
        return ""
    return format(value, fmt)


@login_required
def account_export_view(request: HttpRequest) -> HttpResponse:
    user = request.user

    vehicles = user.vehicles.order_by("id")
    fillups = (
        FillUp.objects.filter(vehicle__user=user)
        .select_related("vehicle")
        .order_by("vehicle_id", "date", "id")
    )

    vehicle_buffer = io.StringIO()
    vehicle_writer = csv.writer(vehicle_buffer)
    vehicle_writer.writerow(
        [
            "id",
            "name",
            "make",
            "model",
            "year",
            "fuel_type",
            "created_at",
            "updated_at",
        ]
    )

    for vehicle in vehicles:
        vehicle_writer.writerow(
            [
                vehicle.id,
                vehicle.name,
                vehicle.make,
                vehicle.model,
                vehicle.year or "",
                vehicle.fuel_type,
                vehicle.created_at.isoformat(),
                vehicle.updated_at.isoformat(),
            ]
        )

    fillup_buffer = io.StringIO()
    fillup_writer = csv.writer(fillup_buffer)
    fillup_writer.writerow(
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
        ]
    )

    currency_code = getattr(getattr(user, "profile", None), "currency", "USD")
    prev_fillup_by_vehicle: dict[int, FillUp] = {}

    for fillup in fillups:
        previous = prev_fillup_by_vehicle.get(fillup.vehicle_id)
        distance_since_last: int | None = None
        consumption: Decimal | None = None
        cost_per_km: Decimal | None = None

        liters = fillup.liters
        total_amount = fillup.total_amount

        unit_price: Decimal | None = None
        if liters > 0:
            unit_price = (total_amount / liters).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        if previous is not None:
            distance_delta = fillup.odometer_km - previous.odometer_km
            if distance_delta > 0:
                distance_since_last = distance_delta
                distance_decimal = Decimal(distance_delta)

                if liters > 0:
                    consumption = (
                        (liters * Decimal("100")) / distance_decimal
                    ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

                if total_amount > 0:
                    cost_per_km = (total_amount / distance_decimal).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

        prev_fillup_by_vehicle[fillup.vehicle_id] = fillup

        fillup_writer.writerow(
            [
                fillup.id,
                fillup.vehicle_id,
                fillup.date.isoformat(),
                fillup.odometer_km,
                fillup.station_name,
                fillup.fuel_brand,
                fillup.fuel_grade,
                format(liters, ".2f"),
                format(total_amount, ".2f"),
                currency_code,
                fillup.notes,
                fillup.created_at.isoformat(),
                fillup.updated_at.isoformat(),
                _format_decimal(unit_price, ".2f"),
                distance_since_last or "",
                _format_decimal(consumption, ".1f"),
                _format_decimal(cost_per_km, ".2f"),
            ]
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("vehicles.csv", vehicle_buffer.getvalue())
        archive.writestr("fillups.csv", fillup_buffer.getvalue())

    zip_buffer.seek(0)
    today = timezone.now().date().strftime("%Y%m%d")
    filename = f"fuel_tracker_export_{user.id}_{today}.zip"

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_http_methods(["GET", "POST"])
def account_delete_view(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "accounts/delete_confirm.html")

    confirmation = request.POST.get("confirm", "").strip()
    if confirmation != "DELETE":
        messages.error(request, "You must type DELETE to confirm account deletion.")
        return render(
            request,
            "accounts/delete_confirm.html",
            {"submitted_value": confirmation},
        )

    user = request.user
    user.delete()
    logout(request)
    messages.success(request, "Your account has been deleted successfully.")
    return redirect("/")
