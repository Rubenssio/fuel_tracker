from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from profiles.models import Profile
from profiles.units import LITERS_PER_GALLON, km_to_miles, liters_to_gallons

from .forms import FillUpForm
from .models import FillUp
from .metrics import aggregate_metrics, per_fill_metrics


def _ensure_profile(user):
    defaults = {
        "currency": "USD",
        "distance_unit": Profile.UNIT_KILOMETERS,
        "volume_unit": Profile.UNIT_LITERS,
        "timezone": "UTC",
        "utc_offset_minutes": 0,
    }
    profile, _ = Profile.objects.get_or_create(user=user, defaults=defaults)
    return profile


class FillUpCreateView(LoginRequiredMixin, CreateView):
    model = FillUp
    form_class = FillUpForm
    template_name = "fillups/form.html"
    success_url = reverse_lazy("vehicle-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        vehicle = form.cleaned_data.get("vehicle")
        if vehicle and vehicle.user != self.request.user:
            form.add_error("vehicle", "You do not have permission to use this vehicle.")
            return self.form_invalid(form)
        return super().form_valid(form)


class FillUpUpdateView(LoginRequiredMixin, UpdateView):
    model = FillUp
    form_class = FillUpForm
    template_name = "fillups/form.html"
    success_url = reverse_lazy("vehicle-list")

    def get_queryset(self):
        return FillUp.objects.filter(vehicle__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        vehicle = form.cleaned_data.get("vehicle")
        if vehicle and vehicle.user != self.request.user:
            form.add_error("vehicle", "You do not have permission to use this vehicle.")
            return self.form_invalid(form)
        return super().form_valid(form)


class FillUpDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("vehicle-list")

    def post(self, request, pk):
        obj = get_object_or_404(FillUp, pk=pk, vehicle__user=request.user)
        obj.delete()
        return redirect(self.success_url)

    def get(self, request, pk):
        return HttpResponseNotAllowed(["POST"])


class HistoryListView(LoginRequiredMixin, ListView):
    model = FillUp
    template_name = "fillups/history.html"
    paginate_by = 25
    context_object_name = "fillups"

    SORT_MAP = {
        "date": "date",
        "odometer": "odometer_km",
        "liters": "liters",
        "total": "total_amount",
    }

    DEFAULT_SORT = "date"
    DEFAULT_DIR = "desc"

    def get_queryset(self):
        request = self.request
        queryset = (
            FillUp.objects.filter(vehicle__user=request.user)
            .select_related("vehicle")
            .order_by("-date", "-id")
        )

        self.active_filters: dict[str, str] = {}

        start_value = request.GET.get("start", "").strip()
        if start_value:
            parsed_start = parse_date(start_value)
            if parsed_start:
                queryset = queryset.filter(date__gte=parsed_start)
                self.active_filters["start"] = start_value

        end_value = request.GET.get("end", "").strip()
        if end_value:
            parsed_end = parse_date(end_value)
            if parsed_end:
                queryset = queryset.filter(date__lte=parsed_end)
                self.active_filters["end"] = end_value

        brand_value = request.GET.get("brand", "").strip()
        if brand_value:
            queryset = queryset.filter(fuel_brand__icontains=brand_value)
            self.active_filters["brand"] = brand_value

        grade_value = request.GET.get("grade", "").strip()
        if grade_value:
            queryset = queryset.filter(fuel_grade__icontains=grade_value)
            self.active_filters["grade"] = grade_value

        station_value = request.GET.get("station", "").strip()
        if station_value:
            queryset = queryset.filter(station_name__icontains=station_value)
            self.active_filters["station"] = station_value

        vehicle_value = request.GET.get("vehicle", "").strip()
        if vehicle_value:
            try:
                vehicle_id = int(vehicle_value)
            except (TypeError, ValueError):
                vehicle_id = None
            else:
                if request.user.vehicles.filter(id=vehicle_id).exists():
                    queryset = queryset.filter(vehicle_id=vehicle_id)
                    self.active_filters["vehicle"] = str(vehicle_id)

        sort_param = request.GET.get("sort", self.DEFAULT_SORT)
        if sort_param not in self.SORT_MAP:
            sort_param = self.DEFAULT_SORT

        dir_param = request.GET.get("dir", self.DEFAULT_DIR)
        if dir_param not in {"asc", "desc"}:
            dir_param = self.DEFAULT_DIR

        self.sort_key = sort_param
        self.sort_dir = dir_param

        sort_field = self.SORT_MAP[sort_param]
        if dir_param == "desc":
            ordering = [f"-{sort_field}", "-id"]
        else:
            ordering = [sort_field, "id"]
        queryset = queryset.order_by(*ordering)

        return queryset

    def _build_querystring(self, **overrides: str) -> str:
        params = {**self.active_filters, "sort": self.sort_key, "dir": self.sort_dir}
        params.update({k: v for k, v in overrides.items() if v is not None})
        # Remove blank values to keep querystrings tidy.
        params = {k: v for k, v in params.items() if str(v)}
        return urlencode(params)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        profile = _ensure_profile(user)
        unit_prefs = {
            "distance": "mi" if profile.distance_unit == Profile.UNIT_MILES else "km",
            "volume": "gal" if profile.volume_unit == Profile.UNIT_GALLONS else "L",
            "currency": profile.currency or "USD",
        }

        page_obj = context.get("page_obj")
        if page_obj is not None:
            page_fillups = list(page_obj.object_list)
        else:
            page_fillups = list(context.get("fillups", []))

        fillup_by_id = {fillup.id: fillup for fillup in page_fillups}

        for fillup in page_fillups:
            fillup._calc = SimpleNamespace(
                distance_since_last=None,
                unit_price=None,
                efficiency=None,
                cost_per_distance=None,
            )

            distance_value = float(fillup.odometer_km)
            if unit_prefs["distance"] == "mi":
                distance_value = km_to_miles(distance_value)
            fillup.display_odometer = int(round(distance_value))

            volume_value = float(fillup.liters)
            if unit_prefs["volume"] == "gal":
                volume_value = liters_to_gallons(volume_value)
            fillup.display_volume = f"{volume_value:.2f}"

            fillup.display_total = f"{unit_prefs['currency']} {fillup.total_amount:.2f}"

        def _fmt_distance_since_last(km_val):
            if km_val is None:
                return None
            value = km_val
            if unit_prefs["distance"] == "mi":
                value = km_to_miles(value)
            return str(int(round(value)))

        def _fmt_unit_price(per_liter):
            if per_liter is None:
                return None
            if unit_prefs["volume"] == "gal":
                value = per_liter * LITERS_PER_GALLON
                return f"{unit_prefs['currency']} {value:.2f} / gal"
            return f"{unit_prefs['currency']} {per_liter:.2f} / L"

        def _fmt_efficiency(l_per_100km, mpg):
            if unit_prefs["distance"] == "mi" and unit_prefs["volume"] == "gal":
                if mpg is None:
                    return None
                return f"{mpg:.1f} MPG"
            if l_per_100km is None:
                return None
            return f"{l_per_100km:.1f} L/100km"

        def _fmt_cost_per_distance(cost_per_km, cost_per_mile):
            if unit_prefs["distance"] == "mi":
                if cost_per_mile is None:
                    return None
                return f"{unit_prefs['currency']} {cost_per_mile:.2f} / mi"
            if cost_per_km is None:
                return None
            return f"{unit_prefs['currency']} {cost_per_km:.2f} / km"

        if fillup_by_id:
            vehicle_ids = {fillup.vehicle_id for fillup in page_fillups}
            if vehicle_ids:
                all_vehicle_entries = (
                    FillUp.objects.filter(vehicle__user=user, vehicle_id__in=vehicle_ids)
                    .select_related("vehicle")
                    .order_by("vehicle_id", "date", "id")
                )

                grouped: dict[int, list[FillUp]] = {}
                for entry in all_vehicle_entries:
                    grouped.setdefault(entry.vehicle_id, []).append(entry)

                for vehicle_id, rows in grouped.items():
                    for per_fill in per_fill_metrics(rows):
                        fillup = fillup_by_id.get(per_fill.fillup.id)
                        if not fillup:
                            continue
                        fillup._calc = SimpleNamespace(
                            distance_since_last=_fmt_distance_since_last(per_fill.distance_since_last_km),
                            unit_price=_fmt_unit_price(per_fill.unit_price_per_liter),
                            efficiency=_fmt_efficiency(
                                per_fill.efficiency_l_per_100km, per_fill.efficiency_mpg
                            ),
                            cost_per_distance=_fmt_cost_per_distance(
                                per_fill.cost_per_km, per_fill.cost_per_mile
                            ),
                        )

        if page_obj is not None:
            page_obj.object_list = page_fillups
        context["object_list"] = page_fillups
        context[self.context_object_name] = page_fillups
        context["unit_prefs"] = unit_prefs

        sort_links = {}
        for key in self.SORT_MAP:
            if self.sort_key == key:
                next_dir = "asc" if self.sort_dir == "desc" else "desc"
            else:
                next_dir = "desc"
            sort_links[key] = self._build_querystring(sort=key, dir=next_dir)

        base_querystring = self._build_querystring()

        context.update(
            {
                "active_filters": self.active_filters,
                "sort": self.sort_key,
                "dir": self.sort_dir,
                "vehicles": user.vehicles.all(),
                "unit_prefs": unit_prefs,
                "sort_links": sort_links,
                "base_querystring": base_querystring,
            }
        )

        return context


class MetricsView(LoginRequiredMixin, TemplateView):
    template_name = "fillups/metrics.html"

    WINDOW_DEFAULT = "30"
    WINDOW_CHOICES = {"30", "90", "ytd"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        user = request.user
        profile = getattr(user, "profile", None)
        prefs = profile or SimpleNamespace(
            distance_unit=Profile.UNIT_KILOMETERS,
            volume_unit=Profile.UNIT_LITERS,
            currency="USD",
        )

        window_param = request.GET.get("window", self.WINDOW_DEFAULT).lower()
        if window_param not in self.WINDOW_CHOICES:
            window_param = self.WINDOW_DEFAULT

        today = date.today()
        if window_param == "90":
            window_start = today - timedelta(days=90)
            window_label = "Last 90 days"
        elif window_param == "ytd":
            window_start = date(today.year, 1, 1)
            window_label = "Year to date"
        else:
            window_start = today - timedelta(days=30)
            window_label = "Last 30 days"

        vehicle_param = request.GET.get("vehicle", "all").strip() or "all"
        selected_vehicle_id: int | None = None
        if vehicle_param != "all":
            try:
                candidate_id = int(vehicle_param)
            except (TypeError, ValueError):
                vehicle_param = "all"
            else:
                if user.vehicles.filter(id=candidate_id).exists():
                    selected_vehicle_id = candidate_id
                else:
                    vehicle_param = "all"

        queryset = (
            FillUp.objects.filter(vehicle__user=user)
            .select_related("vehicle")
            .order_by("vehicle_id", "date", "id")
        )
        if selected_vehicle_id is not None:
            queryset = queryset.filter(vehicle_id=selected_vehicle_id)

        entries = list(queryset)

        rolling_raw = aggregate_metrics(entries, window_start=window_start)
        all_time_raw = aggregate_metrics(entries)

        rolling_display = round_for_display(rolling_raw, prefs)
        all_time_display = round_for_display(all_time_raw, prefs)

        context.update(
            {
                "vehicles": user.vehicles.all(),
                "selected_vehicle": vehicle_param,
                "window": window_param,
                "window_label": window_label,
                "rolling_metrics": rolling_display,
                "all_time_metrics": all_time_display,
                "unit_prefs": {
                    "distance": prefs.distance_unit,
                    "volume": prefs.volume_unit,
                    "currency": prefs.currency,
                },
            }
        )

        return context
