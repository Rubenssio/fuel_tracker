"""Reusable mixins for enforcing per-user data ownership."""
from __future__ import annotations

from django.http import Http404


class OwnedQuerysetMixin:
    """Limit querysets and objects to the authenticated user when possible."""

    owner_attribute = "user"

    def get_queryset(self):  # type: ignore[override]
        queryset = super().get_queryset()  # type: ignore[misc]
        model = getattr(queryset, "model", None)
        if model is None:
            return queryset
        if hasattr(model, self.owner_attribute):
            return queryset.filter(**{self.owner_attribute: self.request.user})
        return queryset

    def get_object(self, queryset=None):  # type: ignore[override]
        obj = super().get_object(queryset)  # type: ignore[misc]
        owner = None
        if hasattr(obj, self.owner_attribute):
            owner = getattr(obj, self.owner_attribute)
        elif hasattr(obj, "vehicle") and hasattr(obj.vehicle, self.owner_attribute):
            owner = getattr(obj.vehicle, self.owner_attribute)
        if owner is not None and owner != self.request.user:
            raise Http404()
        return obj
