from __future__ import annotations

from django.contrib import admin

from .models import AuthEvent


@admin.register(AuthEvent)
class AuthEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "email", "created_at")
    list_filter = ("event_type",)
    search_fields = ("email", "user__email")
    ordering = ("-created_at",)
