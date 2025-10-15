from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class LetterNumberPasswordValidator:
    """Ensure at least one letter and one digit are present."""

    def validate(self, password: str, user: Any = None) -> None:  # noqa: D401
        if not re.search(r"[A-Za-z]", password):
            raise ValidationError(_("Password must contain at least one letter."))
        if not re.search(r"\d", password):
            raise ValidationError(_("Password must contain at least one number."))

    def get_help_text(self) -> str:
        return _("Your password must contain at least one letter and one number.")
