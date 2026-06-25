import json
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.orders.models import Order
from apps.videos.models import Video, VideoPurchase
from apps.marketing.models import Advertisement
from apps.support.models import SupportTicket
from .services import get_marketplace_analytics
from .permissions import staff_required


@staff_required
def analytics_center(request):
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    stats = get_marketplace_analytics()

    daily_revenue = []
    labels = []
    for i in range(14, -1, -1):
        day = (now - timedelta(days=i)).date()
        labels.append(day.strftime('%d.%m'))
        rev = Order.objects.filter(
            status='PAID', created_at__date=day
        ).aggregate(s=Sum('final_amount'))['s'] or 0
        daily_revenue.append(float(rev))

    top_products = Video.objects.order_by('-sales_count')[:10]
    top_categories = Video.objects.values('category__name').annotate(
        cnt=Count('id')
    ).order_by('-cnt')[:8]

    context = {
        **stats,
        'labels_json': json.dumps(labels),
        'daily_revenue_json': json.dumps(daily_revenue),
        'new_users_30d': User.objects.filter(date_joined__gte=last_30).count(),
        'video_sales': VideoPurchase.objects.filter(purchased_at__gte=last_30).count(),
        'top_products': top_products,
        'top_categories': top_categories,
        'open_tickets': SupportTicket.objects.filter(status='OPEN').count(),
        'active_ads': Advertisement.objects.filter(is_active=True).count(),
    }
    return render(request, 'adminpanel/analytics/center.html', context)