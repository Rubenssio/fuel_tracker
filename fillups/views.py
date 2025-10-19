from __future__ import annotations

from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from profiles.models import Profile
from profiles.units import km_to_miles, liters_to_gallons

from .forms import FillUpForm
from .models import FillUp


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
        profile = getattr(user, "profile", None)
        unit_prefs = {
            "distance": profile.distance_unit if profile else Profile.UNIT_KILOMETERS,
            "volume": profile.volume_unit if profile else Profile.UNIT_LITERS,
            "currency": profile.currency if profile else "USD",
        }

        fillups = context.get("fillups", [])
        for fillup in fillups:
            distance_value = float(fillup.odometer_km)
            if unit_prefs["distance"] == Profile.UNIT_MILES:
                distance_value = km_to_miles(distance_value)
            fillup.display_odometer = int(round(distance_value))

            volume_value = float(fillup.liters)
            if unit_prefs["volume"] == Profile.UNIT_GALLONS:
                volume_value = liters_to_gallons(volume_value)
            fillup.display_volume = f"{volume_value:.2f}"

            fillup.display_total = f"{unit_prefs['currency']} {fillup.total_amount:.2f}"

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
