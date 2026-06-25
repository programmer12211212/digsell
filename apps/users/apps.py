from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        import apps.users.signals  # noqa: F401
        # Auto-provision Google SocialApp when env vars are present (helps local/dev)
        try:
            import os
            from django.conf import settings
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site

            client_id = os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('SOCIAL_GOOGLE_CLIENT_ID')
            secret = os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('SOCIAL_GOOGLE_CLIENT_SECRET')
            if client_id and secret:
                site = Site.objects.filter(id=getattr(settings, 'SITE_ID', 1)).first()
                if site:
                    app, created = SocialApp.objects.get_or_create(provider='google', defaults={
                        'name': 'Google',
                        'client_id': client_id,
                        'secret': secret,
                    })
                    if site not in app.sites.all():
                        app.sites.add(site)
                        app.save()
        except Exception:
            # don't crash on migrations or missing dependencies
            pass
