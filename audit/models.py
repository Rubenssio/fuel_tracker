from __future__ import annotations

from django.db import models


class AuthEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login Success"
        LOGIN_FAILED = "login_failed", "Login Failed"
        LOGOUT = "logout", "Logout"
        SIGNUP = "signup", "Signup"

    event_type = models.CharField(
        max_length=32,
        choices=EventType.choices,
    )
    user = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="auth_events",
    )
    email = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    correlation_id = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        user_display = self.user_id if self.user_id is not None else "-"
        return f"AuthEvent({self.event_type}, user={user_display})"
