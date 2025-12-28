from django.apps import AppConfig


class BasketballConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "basketball"

    def ready(self):
        # Importar extensiones de spectacular para que se registren
        try:
            import basketball.spectacular_extensions  # noqa: F401
        except ImportError:
            pass
