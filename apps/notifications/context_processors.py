from apps.notifications.models import Notification

def notifications_ctx(request):
    """Barcha sahifalarda bildirishnomalarni ko'rsatish uchun."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifs,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
