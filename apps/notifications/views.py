from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read(request, notif_id):
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    messages.success(request, "Bildirishnoma o'qildi deb belgilandi.")
    return redirect(request.META.get('HTTP_REFERER') or reverse('notifications:list'))


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "Barcha bildirishnomalar o'qildi.")
    return redirect(request.META.get('HTTP_REFERER') or reverse('notifications:list'))
