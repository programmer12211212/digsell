from django.apps import AppConfig


class TelegramServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.telegram_services'
    verbose_name = 'Telegram Services'

    def ready(self):
        import apps.telegram_services.signals
