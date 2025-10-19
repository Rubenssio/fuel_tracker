from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest

from core.logging import cv_correlation_id

from .models import AuthEvent

User = get_user_model()


def _get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        for value in forwarded.split(","):
            candidate = value.strip()
            if candidate:
                return candidate
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request: Optional[HttpRequest]) -> str:
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


def _get_correlation_id(request: Optional[HttpRequest]) -> str:
    if request is not None:
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id:
            return str(correlation_id)
    context_value = cv_correlation_id.get(None)
    if context_value:
        return str(context_value)
    return ""


def _create_event(
    *,
    event_type: str,
    request: Optional[HttpRequest],
    user: Optional[User] = None,
    email: str = "",
) -> None:
    AuthEvent.objects.create(
        event_type=event_type,
        user=user,
        email=email or "",
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        correlation_id=_get_correlation_id(request),
    )


@receiver(user_logged_in)
def handle_user_logged_in(  # noqa: D401
    sender, request: HttpRequest, user: User, **kwargs
) -> None:
    _create_event(
        event_type=AuthEvent.EventType.LOGIN_SUCCESS,
        request=request,
        user=user,
    )


@receiver(user_logged_out)
def handle_user_logged_out(  # noqa: D401
    sender, request: HttpRequest, user: User, **kwargs
) -> None:
    _create_event(
        event_type=AuthEvent.EventType.LOGOUT,
        request=request,
        user=user,
    )


@receiver(user_login_failed)
def handle_user_login_failed(  # noqa: D401
    sender, credentials, request: Optional[HttpRequest], **kwargs
) -> None:
    email = credentials.get("email") or credentials.get("username") or ""
    _create_event(
        event_type=AuthEvent.EventType.LOGIN_FAILED,
        request=request,
        email=email,
    )
