from django.apps import AppConfig


class FreelanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.freelance"
    verbose_name = "Freelance"

    def ready(self):
        import apps.freelance.signals  # noqa: F401
