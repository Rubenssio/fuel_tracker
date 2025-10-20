from django.urls import path

from .views import (
    SigninView,
    SignoutView,
    SignupView,
    account_delete_view,
    account_export_view,
)

app_name = "accounts"

urlpatterns = [
    path("auth/signup", SignupView.as_view(), name="signup"),
    path("auth/signin", SigninView.as_view(), name="signin"),
    path("auth/signout", SignoutView.as_view(), name="signout"),
    path("account/export", account_export_view, name="export"),
    path("account/delete", account_delete_view, name="delete"),
]
