from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.notifications.models import Notification
from .services import get_admin_notifications
from .permissions import staff_required


@staff_required
def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, 'adminpanel/notifications/center.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@staff_required
def notification_api(request):
    return JsonResponse(get_admin_notifications(request.user))


@require_POST
@staff_required
def mark_notification_read(request, notif_id):
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({'success': True})


@require_POST
@staff_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})