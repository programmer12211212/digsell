from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

from .services import get_server_stats, get_marketplace_analytics
from .permissions import staff_required


@staff_required
def monitoring_center(request):
    server = get_server_stats()
    analytics = get_marketplace_analytics()

    celery_status = 'Noma\'lum'
    redis_status = 'Noma\'lum'
    db_status = 'OK'

    try:
        from django.core.cache import cache
        cache.set('_health', 'ok', 10)
        redis_status = 'OK' if cache.get('_health') == 'ok' else 'Xato'
    except Exception:
        redis_status = 'Ulanmagan'

    try:
        from django.db import connection
        connection.ensure_connection()
        db_status = 'OK'
    except Exception:
        db_status = 'Xato'

    return render(request, 'adminpanel/monitoring/center.html', {
        'server': server,
        'analytics': analytics,
        'celery_status': celery_status,
        'redis_status': redis_status,
        'db_status': db_status,
        'debug_mode': settings.DEBUG,
    })