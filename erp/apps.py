from django.apps import AppConfig


class ErpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "erp"

    def ready(self):
        # Conecta señales de auditoría (login/logout).
        from . import auditoria  # noqa: F401

