from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

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
