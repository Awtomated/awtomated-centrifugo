from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

REQUIRED_SETTINGS = [
    "CENTRIFUGO_API_URL",
    "CENTRIFUGO_API_KEY",
    "CENTRIFUGO_TOKEN_HMAC_SECRET",
]


class CentrifugoToolkitConfig(AppConfig):
    name = "centrifugo_toolkit.django_app"
    label = "centrifugo_toolkit"
    verbose_name = "Centrifugo Toolkit"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.conf import settings

        import centrifugo_toolkit

        missing = [name for name in REQUIRED_SETTINGS if not getattr(settings, name, None)]
        if missing:
            raise ImproperlyConfigured(
                "centrifugo_toolkit requires the following settings to be set: " +
                ", ".join(missing)
            )

        centrifugo_toolkit.configure(
            api_url=settings.CENTRIFUGO_API_URL,
            api_key=settings.CENTRIFUGO_API_KEY,
            timeout=getattr(settings, "CENTRIFUGO_TIMEOUT", 5.0),
            max_retries=getattr(settings, "CENTRIFUGO_MAX_RETRIES", 2),
        )
