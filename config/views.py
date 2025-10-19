"""Views for config-level concerns such as error handlers."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def error_400(request: HttpRequest, exception: Exception) -> HttpResponse:  # pragma: no cover
    return render(request, "errors/400.html", status=400)


def error_403(request: HttpRequest, exception: Exception) -> HttpResponse:  # pragma: no cover
    return render(request, "errors/403.html", status=403)


def error_404(request: HttpRequest, exception: Exception) -> HttpResponse:  # pragma: no cover
    return render(request, "errors/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:  # pragma: no cover
    return render(request, "errors/500.html", status=500)
