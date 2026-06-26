import logging

from django.contrib.sessions.exceptions import SessionInterrupted
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class SessionInterruptedMiddleware:
    """Handle session interruption gracefully.

    Django may raise SessionInterrupted when the request's session is deleted before
    the response is finished, typically due to a concurrent logout or session flush.
    This middleware catches that exception and redirects users to login instead of
    surfacing a server error.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except SessionInterrupted as exc:
            logger.warning(
                'Session interrupted on request %s: %s',
                request.path,
                exc,
                exc_info=True,
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Sessiyangiz o‘chirildi. Iltimos, qaytadan kirishingiz kerak.'},
                    status=403,
                )

            return redirect(reverse('users:login'))

        return response
