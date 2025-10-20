from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from core.mixins import OwnedQuerysetMixin

from .forms import VehicleForm
from .models import Vehicle


class VehicleListView(LoginRequiredMixin, OwnedQuerysetMixin, ListView):
    model = Vehicle
    template_name = "vehicles/list.html"

    def get_queryset(self):
        return super().get_queryset().order_by("name", "id")


class VehicleCreateView(LoginRequiredMixin, OwnedQuerysetMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicles/form.html"
    success_url = reverse_lazy("vehicle-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class VehicleUpdateView(LoginRequiredMixin, OwnedQuerysetMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicles/form.html"
    success_url = reverse_lazy("vehicle-list")

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class VehicleDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("vehicle-list")

    def post(self, request, pk):
        obj = get_object_or_404(Vehicle, pk=pk, user=request.user)
        obj.delete()
        messages.success(request, "Vehicle deleted.")
        return redirect(self.success_url)

    def get(self, request, pk):
        return HttpResponseNotAllowed(["POST"])
