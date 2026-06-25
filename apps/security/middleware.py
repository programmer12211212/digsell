"""
Xavfsizlik middleware moduli.
Login brute-force, bloklangan IP va shubhali so'rovlarni tekshiradi.
"""
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.utils import timezone

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 daqiqa (soniyalarda)


class BruteForceProtectionMiddleware:
    """
    Login sahifasida ko'p marta noto'g'ri parol kiritishdan himoya qiladi.
    5 marta xato qilsa, 15 daqiqaga bloklanadi.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ('/auth/login/', '/admin/login/') and request.method == 'POST':
            ip = self._get_ip(request)
            cache_key = f'login_attempts_{ip}'
            attempts = cache.get(cache_key, 0)

            if attempts >= MAX_LOGIN_ATTEMPTS:
                # Log the blocked attempt
                self._log_blocked(ip)
                return HttpResponseForbidden(
                    '<div style="text-align:center;padding:60px;font-family:sans-serif;background:#0f172a;color:#f87171;min-height:100vh;">'
                    '<h1>⛔ Kirish bloklandi</h1>'
                    f'<p>Ko\'p marta noto\'g\'ri parol kiritdingiz. {LOCKOUT_DURATION // 60} daqiqa kutib, qayta urinib ko\'ring.</p>'
                    '<p style="color:#64748b;margin-top:20px;">IP manzilingiz: ' + ip + '</p>'
                    '</div>'
                )

        response = self.get_response(request)

        # Agar login muvaffaqiyatsiz bo'lsa, urinishlar sonini oshiramiz
        if request.path in ('/auth/login/', '/admin/login/') and request.method == 'POST':
            if response.status_code != 302:  # Redirect bo'lmasa = xato parol
                ip = self._get_ip(request)
                cache_key = f'login_attempts_{ip}'
                attempts = cache.get(cache_key, 0)
                cache.set(cache_key, attempts + 1, LOCKOUT_DURATION)

        return response

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _log_blocked(self, ip):
        try:
            from apps.security.models import SecurityLog
            SecurityLog.objects.create(
                level='WARNING',
                action='Brute-force urinish bloklandi',
                ip_address=ip,
                details={'reason': f'{MAX_LOGIN_ATTEMPTS} marta noto\'g\'ri parol'}
            )
        except Exception:
            pass


class BlockedIPMiddleware:
    """
    Admin panel orqali bloklangan IP manzillarni tekshiradi.
    Agar IP bloklangan bo'lsa, saytga kirish taqiqlanadi.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_ip(request)

        # Cache orqali tezkor tekshirish
        cache_key = f'blocked_ip_{ip}'
        is_blocked = cache.get(cache_key)

        if is_blocked is None:
            # Bazadan tekshirish
            try:
                from apps.security.models import BlockedIP
                is_blocked = BlockedIP.objects.filter(ip_address=ip).exists()
                cache.set(cache_key, is_blocked, 300)  # 5 daqiqa kesh
            except Exception:
                is_blocked = False

        if is_blocked:
            return HttpResponseForbidden(
                '<div style="text-align:center;padding:60px;font-family:sans-serif;background:#0f172a;color:#f87171;min-height:100vh;">'
                '<h1>🚫 Kirish taqiqlangan</h1>'
                '<p>Sizning IP manzilingiz bloklangan. Admin bilan bog\'laning.</p>'
                '</div>'
            )

        return self.get_response(request)

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
