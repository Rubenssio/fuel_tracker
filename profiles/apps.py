from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

    def ready(self) -> None:  # pragma: no cover - import side-effects only
        from . import signals  # noqa: F401

        return super().ready()
