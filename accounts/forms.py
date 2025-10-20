from __future__ import annotations

import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SignupForm(forms.Form):
    email = forms.EmailField(label=_("Email"))
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        strip=False,
        help_text=_("Minimum 8 characters with at least one letter and one number."),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput,
        strip=False,
    )

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
        "password_letter": _("Password must contain at least one letter."),
        "password_digit": _("Password must contain at least one number."),
    }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def _validate_password_strength(self, password: str) -> None:
        if len(password) < 8:
            raise ValidationError(_("Password must be at least 8 characters long."))
        if not re.search(r"[A-Za-z]", password):
            raise ValidationError(self.error_messages["password_letter"], code="password_no_letter")
        if not re.search(r"\d", password):
            raise ValidationError(self.error_messages["password_digit"], code="password_no_digit")

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1 is None:
            return password1
        self._validate_password_strength(password1)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError({"password2": self.error_messages["password_mismatch"]})
        return cleaned_data

    def save(self):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        return User.objects.create_user(email=email, password=password)


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"))
