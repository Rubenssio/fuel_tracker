"""Navigation helpers for templates."""
from __future__ import annotations

from typing import Any

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_items(context: template.Context) -> list[dict[str, Any]]:
    """Return navigation items with active state for the current request."""
    request = context.get("request")
    path = getattr(request, "path", "/")
    match = getattr(request, "resolver_match", None)
    current_view = getattr(match, "view_name", "") if match else ""
    current_name = getattr(match, "url_name", "") if match else ""

    config = [
        {
            "name": "Home",
            "url_name": "home",
            "icon": "home",
            "matches": {"home"},
        },
        {
            "name": "Vehicles",
            "url_name": "vehicle-list",
            "icon": "car",
            "matches": {
                "vehicle-list",
                "vehicle-add",
                "vehicle-edit",
                "vehicle-delete",
            },
        },
        {
            "name": "History",
            "url_name": "history-list",
            "icon": "gas",
            "matches": {"history-list", "fillup-edit", "fillup-delete", "fillup-add"},
        },
        {
            "name": "Metrics",
            "url_name": "metrics",
            "icon": "chart",
            "matches": {"metrics"},
        },
        {
            "name": "Statistics",
            "url_name": "statistics",
            "icon": "chart",
            "matches": {"statistics"},
        },
        {
            "name": "Settings",
            "url_name": "profiles:settings",
            "icon": "cog",
            "matches": {"profiles:settings", "settings"},
        },
    ]

    items: list[dict[str, Any]] = []

    for entry in config:
        url = reverse(entry["url_name"])
        matches = entry["matches"]

        active = False
        if entry["url_name"] == "home":
            active = path == "/" or current_name == "home" or current_view == "home"
        else:
            if current_name in matches or current_view in matches:
                active = True
            elif path.startswith(url):
                active = True

        items.append(
            {
                "name": entry["name"],
                "url": url,
                "icon": entry["icon"],
                "active": active,
            }
        )

    return items
