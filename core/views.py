"""Views for the bootstrap service."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse


def success_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("success", content_type="text/plain")


def health_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})
