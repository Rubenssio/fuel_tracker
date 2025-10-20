"""Custom middleware for lightweight security headers and observability."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from .logging import cv_correlation_id


class CorrelationIdMiddleware:
    """Ensure each request is associated with a correlation identifier."""

    header_name = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        header_value = request.META.get(self.header_name, "")
        inbound_id = header_value.strip() if header_value else ""
        correlation_id = inbound_id or uuid.uuid4().hex
        request.correlation_id = correlation_id
        token = cv_correlation_id.set(correlation_id)
        try:
            response = self.get_response(request)
        finally:
            cv_correlation_id.reset(token)
        response["X-Request-ID"] = correlation_id
        return response


class SecurityHeadersMiddleware:
    """Attach a small set of security-focused response headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if not settings.DEBUG:
            response.setdefault("Content-Security-Policy", "default-src 'self'")
        return response
