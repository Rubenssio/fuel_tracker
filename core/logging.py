"""Logging helpers and request context management."""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

cv_correlation_id: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)
cv_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
cv_request_path: ContextVar[str | None] = ContextVar("request_path", default=None)
cv_request_method: ContextVar[str | None] = ContextVar(
    "request_method", default=None
)
cv_status_code: ContextVar[int | None] = ContextVar("status_code", default=None)


class RequestContextFilter(logging.Filter):
    """Inject context-local request information into log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.correlation_id = self._resolve_value(
            record, "correlation_id", cv_correlation_id.get(None)
        )
        record.user_id = self._resolve_value(
            record, "user_id", cv_user_id.get(None)
        )
        record.request_method = self._resolve_value(
            record, "request_method", cv_request_method.get(None)
        )
        record.request_path = self._resolve_value(
            record, "request_path", cv_request_path.get(None)
        )
        record.status_code = self._resolve_value(
            record, "status_code", cv_status_code.get(None)
        )
        return True

    @staticmethod
    def _resolve_value(
        record: logging.LogRecord, attribute: str, context_value: Any
    ) -> str:
        if hasattr(record, attribute):
            value = getattr(record, attribute)
            if value not in (None, ""):
                return str(value)
        if attribute == "correlation_id":
            request = getattr(record, "request", None)
            if request is not None:
                correlation_id = getattr(request, "correlation_id", None)
                if correlation_id:
                    return str(correlation_id)
        if attribute == "user_id":
            request = getattr(record, "request", None)
            if request is not None:
                user = getattr(request, "user", None)
                if getattr(user, "is_authenticated", False):
                    return str(getattr(user, "pk", "-"))
        if attribute == "request_method":
            request = getattr(record, "request", None)
            if request is not None and getattr(request, "method", None):
                return str(request.method)
        if attribute == "request_path":
            request = getattr(record, "request", None)
            if request is not None and getattr(request, "path", None):
                return str(request.path)
        if attribute == "status_code":
            status = getattr(record, "status_code", None)
            if status not in (None, ""):
                return str(status)
        if context_value not in (None, ""):
            return str(context_value)
        return "-"


class FinalizeRequestLoggingMiddleware:
    """Capture request metadata for structured logging."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("core.request")

    def __call__(self, request):
        method_token = cv_request_method.set(request.method)
        path_token = cv_request_path.set(request.path)
        user_id = "-"
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            user_id = str(getattr(user, "pk", "-"))
        user_token = cv_user_id.set(user_id)
        refreshed_user_token = None

        status_token = None
        try:
            response = self.get_response(request)
        except Exception:
            refreshed_user_token = self._refresh_user_context(request)
            status_token = cv_status_code.set(500)
            self.logger.info("request_finished")
            raise
        else:
            refreshed_user_token = self._refresh_user_context(request)
            status_token = cv_status_code.set(response.status_code)
            self.logger.info("request_finished")
            return response
        finally:
            if status_token is not None:
                cv_status_code.reset(status_token)
            if refreshed_user_token is not None:
                cv_user_id.reset(refreshed_user_token)
            cv_user_id.reset(user_token)
            cv_request_path.reset(path_token)
            cv_request_method.reset(method_token)

    @staticmethod
    def _refresh_user_context(request):
        user = getattr(request, "user", None)
        user_id = "-"
        if getattr(user, "is_authenticated", False):
            user_id = str(getattr(user, "pk", "-"))
        if cv_user_id.get(None) == user_id:
            return None
        return cv_user_id.set(user_id)
