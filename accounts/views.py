from __future__ import annotations

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import EmailAuthenticationForm, SignupForm


class SignupView(View):
    template_name = "accounts/signup.html"
    form_class = SignupForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("success")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("success")
        return render(request, self.template_name, {"form": form})


class SigninView(LoginView):
    template_name = "accounts/signin.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("success")
        return super().dispatch(request, *args, **kwargs)


class SignoutView(LogoutView):
    next_page = reverse_lazy("success")
