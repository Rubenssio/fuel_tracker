from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from profiles.models import Profile
from profiles.units import gallons_to_liters, km_to_miles, liters_to_gallons
from core.mixins import OwnedQuerysetMixin
from core.utils import sanitize_next

from .forms import FillUpForm
from .models import FillUp
from .metrics import aggregate_metrics, per_fill_metrics
from .stats import (
    brand_grade_summary,
    timeseries_consumption,
    timeseries_cost_per_liter,
    to_svg_path,
    window_start_from_param,
)


def _ensure_profile(user):
    defaults = {
        "currency": "USD",
        "distance_unit": Profile.UNIT_KILOMETERS,
        "volume_unit": Profile.UNIT_LITERS,
        "efficiency_unit": Profile.EfficiencyUnit.L_PER_100KM,
        "timezone": "UTC",
        "utc_offset_minutes": 0,
    }
    profile, _ = Profile.objects.get_or_create(user=user, defaults=defaults)
    return profile


class FillUpFormContextMixin:
    def _option_values(self, field_name: str) -> list[str]:
        queryset = (
            FillUp.objects.filter(user=self.request.user)
            .exclude(**{field_name: ""})
            .order_by()
            .values_list(field_name, flat=True)
            .distinct()
        )
        return list(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "brand_options": self._option_values("fuel_brand"),
                "grade_options": self._option_values("fuel_grade"),
                "station_options": self._option_values("station_name"),
            }
        )
        return context


class FillUpCreateView(LoginRequiredMixin, OwnedQuerysetMixin, FillUpFormContextMixin, CreateView):
    model = FillUp
    form_class = FillUpForm
    template_name = "fillups/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_raw = self.request.GET.get("next") or self.request.POST.get("next")
        next_url = sanitize_next(next_raw, default="/vehicles")
        context["next_url"] = next_url
        context["cancel_url"] = next_url
        return context

    def form_valid(self, form):
        vehicle = form.cleaned_data.get("vehicle") or getattr(form.instance, "vehicle", None)
        if vehicle is None or vehicle.user != self.request.user:
            raise Http404()
        self.object = form.save()
        return redirect(sanitize_next(self.request.POST.get("next"), default="/vehicles"))


class FillUpUpdateView(LoginRequiredMixin, OwnedQuerysetMixin, FillUpFormContextMixin, UpdateView):
    model = FillUp
    form_class = FillUpForm
    template_name = "fillups/form.html"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_raw = self.request.GET.get("next") or self.request.POST.get("next")
        next_url = sanitize_next(next_raw, default="/vehicles")
        context["next_url"] = next_url
        context["cancel_url"] = next_url
        return context

    def form_valid(self, form):
        vehicle = form.cleaned_data.get("vehicle") or getattr(form.instance, "vehicle", None)
        if vehicle is None or vehicle.user != self.request.user:
            raise Http404()
        self.object = form.save()
        return redirect(sanitize_next(self.request.POST.get("next"), default="/vehicles"))


class FillUpDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(FillUp, pk=pk, user=request.user)
        obj.delete()
        return redirect(sanitize_next(request.POST.get("next"), default="/history"))

    def get(self, request, pk):
        return HttpResponseNotAllowed(["POST"])


class HistoryListView(LoginRequiredMixin, OwnedQuerysetMixin, ListView):
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
        queryset = super().get_queryset()
        queryset = (
            queryset.filter(user=request.user)
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
        efficiency_unit_choice = profile.efficiency_unit
        efficiency_label = (
            "MPG"
            if efficiency_unit_choice == Profile.EfficiencyUnit.MPG
            else "L/100km"
        )

        page_obj = context.get("page_obj")
        if page_obj is not None:
            page_fillups = list(page_obj.object_list)
        else:
            page_fillups = list(context.get("fillups", []))

        fillup_by_id = {fillup.id: fillup for fillup in page_fillups}

        liters_per_gallon = Decimal(str(gallons_to_liters(1.0)))

        for fillup in page_fillups:
            fillup.calc = SimpleNamespace(
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

        def _fmt_distance_since_last(km_val: float | None):
            if km_val is None:
                return None
            value = km_val
            if unit_prefs["distance"] == "mi":
                value = km_to_miles(value)
            return str(int(round(value)))

        def _fmt_unit_price(per_liter: Decimal | None):
            if per_liter is None:
                return None
            value = per_liter
            unit_label = "L"
            if unit_prefs["volume"] == "gal":
                value = per_liter * liters_per_gallon
                unit_label = "gal"
            return f"{unit_prefs['currency']} {value:.2f} / {unit_label}"

        def _fmt_efficiency(l_per_100km: float | None, mpg: float | None):
            if efficiency_unit_choice == Profile.EfficiencyUnit.MPG:
                if mpg is None:
                    return None
                return f"{mpg:.1f} {efficiency_label}"
            if l_per_100km is None:
                return None
            return f"{l_per_100km:.1f} {efficiency_label}"

        def _fmt_cost_per_distance(cost_per_km: Decimal | None, cost_per_mile: Decimal | None):
            currency = unit_prefs["currency"]
            if unit_prefs["distance"] == "mi":
                if cost_per_mile is None:
                    return None
                value = cost_per_mile
                return f"{currency} {value:.2f} / mi"
            if cost_per_km is None:
                return None
            return f"{currency} {cost_per_km:.2f} / km"

        if fillup_by_id:
            vehicle_ids = {fillup.vehicle_id for fillup in page_fillups}
            if vehicle_ids:
                all_vehicle_entries = (
                    FillUp.objects.filter(user=user, vehicle_id__in=vehicle_ids)
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
                        fillup.calc = SimpleNamespace(
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
        context["efficiency_label"] = efficiency_label

        sort_links = {}
        for key in self.SORT_MAP:
            if self.sort_key == key:
                next_dir = "asc" if self.sort_dir == "desc" else "desc"
            else:
                next_dir = "desc"
            sort_links[key] = self._build_querystring(sort=key, dir=next_dir)

        base_querystring = self._build_querystring()

        brand_options = (
            FillUp.objects.filter(user=user)
            .exclude(fuel_brand="")
            .values_list("fuel_brand", flat=True)
            .distinct()
            .order_by("fuel_brand")
        )
        grade_options = (
            FillUp.objects.filter(user=user)
            .exclude(fuel_grade="")
            .values_list("fuel_grade", flat=True)
            .distinct()
            .order_by("fuel_grade")
        )
        station_options = (
            FillUp.objects.filter(user=user)
            .exclude(station_name="")
            .values_list("station_name", flat=True)
            .distinct()
            .order_by("station_name")
        )

        context.update(
            {
                "active_filters": self.active_filters,
                "sort": self.sort_key,
                "dir": self.sort_dir,
                "vehicles": user.vehicles.all(),
                "unit_prefs": unit_prefs,
                "sort_links": sort_links,
                "base_querystring": base_querystring,
                "efficiency_label": efficiency_label,
                "brand_options": list(brand_options),
                "grade_options": list(grade_options),
                "station_options": list(station_options),
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
        profile = _ensure_profile(user)
        prefs = profile

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
            FillUp.objects.filter(user=user)
            .select_related("vehicle")
            .order_by("vehicle_id", "date", "id")
        )
        if selected_vehicle_id is not None:
            queryset = queryset.filter(vehicle_id=selected_vehicle_id)

        entries = list(queryset)

        rolling_raw = aggregate_metrics(entries, window_start=window_start)
        all_time_raw = aggregate_metrics(entries)

        unit_prefs = {
            "distance": "mi" if prefs.distance_unit == Profile.UNIT_MILES else "km",
            "volume": "gal" if prefs.volume_unit == Profile.UNIT_GALLONS else "L",
            "currency": prefs.currency or "USD",
        }
        efficiency_unit_choice = prefs.efficiency_unit
        efficiency_label = (
            "MPG"
            if efficiency_unit_choice == Profile.EfficiencyUnit.MPG
            else "L/100km"
        )

        liters_per_gallon = Decimal(str(gallons_to_liters(1.0)))

        def _format_metrics(raw: dict) -> dict[str, str | None]:
            result: dict[str, str | None] = {
                "avg_cost_per_volume": None,
                "avg_consumption": None,
                "avg_distance_per_day": None,
                "avg_cost_per_distance": None,
                "total_spend": f"{unit_prefs['currency']} {raw['total_spend']:.2f}",
                "total_distance": f"0 {unit_prefs['distance']}",
            }

            avg_cost_per_liter = raw.get("avg_cost_per_liter")
            if avg_cost_per_liter is not None:
                value = avg_cost_per_liter
                unit_label = "L"
                if unit_prefs["volume"] == "gal":
                    value = avg_cost_per_liter * liters_per_gallon
                    unit_label = "gal"
                result["avg_cost_per_volume"] = f"{unit_prefs['currency']} {value:.2f} / {unit_label}"

            if efficiency_unit_choice == Profile.EfficiencyUnit.MPG:
                mpg = raw.get("avg_consumption_mpg")
                if mpg is not None:
                    result["avg_consumption"] = f"{mpg:.1f} {efficiency_label}"
            else:
                l_per_100 = raw.get("avg_consumption_l_per_100km")
                if l_per_100 is not None:
                    result["avg_consumption"] = f"{l_per_100:.1f} {efficiency_label}"

            avg_distance_per_day = raw.get("avg_distance_per_day_km")
            if avg_distance_per_day is not None:
                value = avg_distance_per_day
                if unit_prefs["distance"] == "mi":
                    value = km_to_miles(value)
                result["avg_distance_per_day"] = f"{int(round(value))} {unit_prefs['distance']}/day"

            if unit_prefs["distance"] == "mi":
                cost_per_mile = raw.get("avg_cost_per_mile")
                if cost_per_mile is not None:
                    result["avg_cost_per_distance"] = f"{unit_prefs['currency']} {cost_per_mile:.2f} / mi"
            else:
                cost_per_km = raw.get("avg_cost_per_km")
                if cost_per_km is not None:
                    result["avg_cost_per_distance"] = f"{unit_prefs['currency']} {cost_per_km:.2f} / km"

            total_distance_km = raw.get("total_distance_km", 0.0) or 0.0
            distance_value = total_distance_km
            if unit_prefs["distance"] == "mi":
                distance_value = km_to_miles(distance_value)
            result["total_distance"] = f"{int(round(distance_value))} {unit_prefs['distance']}"

            return result

        rolling_display = _format_metrics(rolling_raw)
        all_time_display = _format_metrics(all_time_raw)

        context.update(
            {
                "vehicles": user.vehicles.all(),
                "selected_vehicle": vehicle_param,
                "window": window_param,
                "window_label": window_label,
                "rolling_metrics": rolling_display,
                "all_time_metrics": all_time_display,
                "unit_prefs": unit_prefs,
                "efficiency_label": efficiency_label,
            }
        )

        return context


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "fillups/statistics.html"

    CHART_WIDTH = 600
    CHART_HEIGHT = 160
    WINDOW_DEFAULT = "30"
    WINDOW_CHOICES = {"30", "90", "ytd", "all"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        user = request.user
        profile = _ensure_profile(user)

        unit_prefs = {
            "distance": "mi" if profile.distance_unit == Profile.UNIT_MILES else "km",
            "volume": "gal" if profile.volume_unit == Profile.UNIT_GALLONS else "L",
            "currency": profile.currency or "USD",
        }
        efficiency_unit_choice = profile.efficiency_unit
        efficiency_label = (
            "MPG"
            if efficiency_unit_choice == Profile.EfficiencyUnit.MPG
            else "L/100km"
        )
        use_mpg = efficiency_unit_choice == Profile.EfficiencyUnit.MPG

        window_param = request.GET.get("window", self.WINDOW_DEFAULT).lower()
        if window_param not in self.WINDOW_CHOICES:
            window_param = self.WINDOW_DEFAULT

        today = date.today()
        window_start = window_start_from_param(window_param, today)

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
            FillUp.objects.filter(user=user)
            .select_related("vehicle")
            .order_by("vehicle_id", "date", "id")
        )
        if selected_vehicle_id is not None:
            queryset = queryset.filter(vehicle_id=selected_vehicle_id)

        entries = list(queryset)
        window_entries = [
            entry for entry in entries if window_start is None or entry.date >= window_start
        ]

        summary_raw = aggregate_metrics(entries, window_start=window_start)

        liters_per_gallon = Decimal(str(gallons_to_liters(1.0)))

        def _format_cost_per_volume(value: Decimal | None) -> str:
            if value is None:
                return "—"
            converted = value
            unit_label = "L"
            if unit_prefs["volume"] == "gal":
                converted = value * liters_per_gallon
                unit_label = "gal"
            return f"{unit_prefs['currency']} {converted:.2f} / {unit_label}"

        def _format_consumption(avg_l_per_100km: float | None, avg_mpg: float | None) -> str:
            if use_mpg:
                if avg_mpg is None:
                    return "—"
                return f"{avg_mpg:.1f} {efficiency_label}"
            if avg_l_per_100km is None:
                return "—"
            return f"{avg_l_per_100km:.1f} {efficiency_label}"

        def _format_cost_per_distance(
            cost_per_km: Decimal | None, cost_per_mile: Decimal | None
        ) -> str:
            currency = unit_prefs["currency"]
            if unit_prefs["distance"] == "mi":
                if cost_per_mile is None:
                    return "—"
                return f"{currency} {cost_per_mile:.2f} / mi"
            if cost_per_km is None:
                return "—"
            return f"{currency} {cost_per_km:.2f} / km"

        total_distance_value = summary_raw.get("total_distance_km", 0.0) or 0.0
        if unit_prefs["distance"] == "mi":
            total_distance_value = km_to_miles(total_distance_value)

        avg_distance_per_day = summary_raw.get("avg_distance_per_day_km")
        if avg_distance_per_day is not None and unit_prefs["distance"] == "mi":
            avg_distance_per_day = km_to_miles(avg_distance_per_day)

        summary = {
            "avg_consumption": _format_consumption(
                summary_raw.get("avg_consumption_l_per_100km"),
                summary_raw.get("avg_consumption_mpg"),
            ),
            "avg_cost_per_volume": _format_cost_per_volume(
                summary_raw.get("avg_cost_per_liter")
            ),
            "total_spend": f"{unit_prefs['currency']} {summary_raw.get('total_spend', Decimal('0')):.2f}",
            "total_distance": f"{int(round(total_distance_value))} {unit_prefs['distance']}",
            "avg_cost_per_distance": _format_cost_per_distance(
                summary_raw.get("avg_cost_per_km"), summary_raw.get("avg_cost_per_mile")
            ),
            "avg_distance_per_day": (
                f"{int(round(avg_distance_per_day))} {unit_prefs['distance']}/day"
                if avg_distance_per_day is not None
                else "—"
            ),
        }

        cost_series_raw = timeseries_cost_per_liter(window_entries)
        cost_series_converted: list[tuple[date, float]] = []
        for entry_date, price_per_liter in cost_series_raw:
            converted = price_per_liter
            if unit_prefs["volume"] == "gal":
                converted = price_per_liter * liters_per_gallon
            cost_series_converted.append((entry_date, float(converted)))

        consumption_series_raw = timeseries_consumption(window_entries)
        consumption_series_converted: list[tuple[date, float | None]] = []
        miles_per_100km = km_to_miles(100.0)
        for entry_date, consumption in consumption_series_raw:
            if consumption is None:
                consumption_series_converted.append((entry_date, None))
                continue
            if use_mpg:
                gallons = liters_to_gallons(consumption)
                value: float | None = None
                if gallons > 0:
                    value = miles_per_100km / gallons
                consumption_series_converted.append((entry_date, value))
            else:
                consumption_series_converted.append((entry_date, consumption))

        def _build_chart(
            series: list[tuple[date, float | None]],
            precision: int,
            unit_label: str,
        ) -> dict:
            cleaned_with_index = [
                (d, v, idx) for idx, (d, v) in enumerate(series) if v is not None
            ]
            if not cleaned_with_index:
                return {
                    "points": [],
                    "path": "",
                    "x_labels": [],
                    "y_min": None,
                    "y_max": None,
                    "unit_label": unit_label,
                    "has_data": False,
                    "width": self.CHART_WIDTH,
                    "height": self.CHART_HEIGHT,
                }

            cleaned_with_index.sort(key=lambda item: (item[0], item[2]))
            dates = [item[0] for item in cleaned_with_index]
            values = [item[1] for item in cleaned_with_index]

            min_date = min(dates)
            max_date = max(dates)
            min_value = min(values)
            max_value = max(values)

            points: list[tuple[float, float]] = []
            if max_date == min_date:
                x_positions = [self.CHART_WIDTH / 2.0] * len(cleaned_with_index)
            else:
                total_days = (max_date - min_date).days
                if total_days == 0:
                    total_days = 1
                x_positions = [
                    ((d - min_date).days / total_days) * self.CHART_WIDTH for d in dates
                ]

            if max_value == min_value:
                points = [(x, self.CHART_HEIGHT / 2.0) for x in x_positions]
            else:
                value_range = max_value - min_value
                scale = self.CHART_HEIGHT / value_range
                for x, value in zip(x_positions, values):
                    y = self.CHART_HEIGHT - ((value - min_value) * scale)
                    points.append((x, y))

            if not points:
                points = [(x_positions[0], self.CHART_HEIGHT / 2.0)]

            unique_dates = []
            for candidate in sorted(set(dates)):
                label = candidate.strftime("%b %d")
                unique_dates.append(label)

            labels: list[str] = []
            if unique_dates:
                labels.append(unique_dates[0])
                if len(unique_dates) > 2:
                    middle = unique_dates[len(unique_dates) // 2]
                    if middle not in {unique_dates[0], unique_dates[-1]}:
                        labels.append(middle)
                if len(unique_dates) > 1:
                    labels.append(unique_dates[-1])

            path = to_svg_path(points)

            return {
                "points": points,
                "path": path,
                "x_labels": labels,
                "y_min": f"{min_value:.{precision}f}",
                "y_max": f"{max_value:.{precision}f}",
                "unit_label": unit_label,
                "has_data": True,
                "width": self.CHART_WIDTH,
                "height": self.CHART_HEIGHT,
            }

        chart_cost = _build_chart(
            [(d, v) for d, v in cost_series_converted],
            precision=2,
            unit_label=f"{unit_prefs['currency']} / {unit_prefs['volume']}",
        )

        consumption_unit = efficiency_label
        chart_consumption = _build_chart(
            consumption_series_converted,
            precision=1,
            unit_label=consumption_unit,
        )

        brand_rows = []
        raw_brand_rows = brand_grade_summary(window_entries)
        for row in raw_brand_rows:
            avg_cost = row.get("avg_cost_per_liter")
            avg_consumption = row.get("avg_consumption_l_per_100km")

            cost_display = _format_cost_per_volume(avg_cost)
            if cost_display == "—" and avg_cost is None:
                cost_display = "—"

            if avg_consumption is None:
                consumption_display = "—"
            elif use_mpg:
                gallons = liters_to_gallons(avg_consumption)
                if gallons > 0:
                    consumption_display = f"{miles_per_100km / gallons:.1f} {efficiency_label}"
                else:
                    consumption_display = "—"
            else:
                consumption_display = f"{avg_consumption:.1f} {efficiency_label}"

            brand_rows.append(
                {
                    "brand": row.get("brand") or "—",
                    "grade": row.get("grade") or "—",
                    "avg_cost_per_volume": cost_display,
                    "avg_consumption": consumption_display,
                    "count": row.get("count", 0),
                }
            )

        vehicles = user.vehicles.all().order_by("name")
        selected_vehicle_value = "all" if selected_vehicle_id is None else str(selected_vehicle_id)

        window_options = ["30", "90", "ytd", "all"]

        context.update(
            {
                "unit_prefs": unit_prefs,
                "selected_vehicle_id": selected_vehicle_id,
                "selected_vehicle": selected_vehicle_value,
                "selected_window": window_param,
                "window_options": window_options,
                "summary": summary,
                "chart_cost": chart_cost,
                "chart_consumption": chart_consumption,
                "brand_rows": brand_rows,
                "vehicles": vehicles,
                "efficiency_label": efficiency_label,
            }
        )

        return context
