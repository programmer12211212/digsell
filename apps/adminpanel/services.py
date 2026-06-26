import platform
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.users.models import User, WalletTransaction
from apps.orders.models import Order
from apps.marketplace.models import Product
from apps.videos.models import Video
from apps.payments.models import Transaction, WithdrawalRequest
from apps.subscriptions.models import UserSubscription
from apps.support.models import SupportTicket
from apps.notifications.models import Notification

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_server_stats():
    if HAS_PSUTIL:
        disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
        return {
            'cpu_usage': psutil.cpu_percent(interval=0.1),
            'ram_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage(disk_path).percent,
            'os': platform.system(),
            'python_version': platform.python_version(),
        }
    return {
        'cpu_usage': 0,
        'ram_usage': 0,
        'disk_usage': 0,
        'os': platform.system(),
        'python_version': platform.python_version(),
    }


def _pct_change(current, previous):
    if not previous:
        return 100.0 if current else 0.0
    return round(((current - previous) / previous) * 100, 1)


def get_dashboard_stats():
    cache_key = 'admin_dashboard_stats'
    cached = cache.get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    prev_week = now - timedelta(days=14)

    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__gte=today_start).count()
    new_users_yesterday = User.objects.filter(
        date_joined__gte=yesterday_start, date_joined__lt=today_start
    ).count()

    active_listings = Product.objects.filter(is_active=True, is_verified=True).count()
    active_listings += Video.objects.published().count()
    pending_listings = Product.objects.filter(is_verified=False, is_active=True).count()
    pending_listings += Video.objects.exclude(moderation_status=Video.ModerationStatus.APPROVED).count()

    orders_today = Order.objects.filter(created_at__gte=today_start).count()
    orders_yesterday = Order.objects.filter(
        created_at__gte=yesterday_start, created_at__lt=today_start
    ).count()

    total_transactions = Transaction.objects.count() + WalletTransaction.objects.count()
    tx_week = Transaction.objects.filter(created_at__gte=week_ago).count()
    tx_prev_week = Transaction.objects.filter(
        created_at__gte=prev_week, created_at__lt=week_ago
    ).count()

    premium_users = UserSubscription.objects.filter(is_active=True).count()
    open_tickets = SupportTicket.objects.filter(
        status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]
    ).count()

    stats = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_listings': active_listings,
        'pending_listings': pending_listings,
        'orders_today': orders_today,
        'total_transactions': total_transactions,
        'premium_users': premium_users,
        'open_tickets': open_tickets,
        'trends': {
            'users': _pct_change(new_users_today, new_users_yesterday),
            'listings': _pct_change(active_listings, max(active_listings - 5, 1)),
            'orders': _pct_change(orders_today, orders_yesterday),
            'transactions': _pct_change(tx_week, tx_prev_week),
            'premium': _pct_change(premium_users, max(premium_users - 1, 0)),
            'tickets': _pct_change(open_tickets, max(open_tickets - 1, 0)),
        },
    }
    cache.set(cache_key, stats, 30)
    return stats


def get_analytics_chart(range_key='30d'):
    ranges = {
        '24h': (timedelta(hours=24), 'hour'),
        '7d': (timedelta(days=7), 'day'),
        '30d': (timedelta(days=30), 'day'),
        '90d': (timedelta(days=90), 'week'),
        '1y': (timedelta(days=365), 'month'),
    }
    delta, granularity = ranges.get(range_key, ranges['30d'])
    start = timezone.now() - delta
    labels = []
    users_data = []
    listings_data = []
    payments_data = []
    orders_data = []

    if granularity == 'hour':
        points = 24
        step = timedelta(hours=1)
    elif granularity == 'day':
        points = min(int(delta.days), 30)
        step = timedelta(days=1)
    elif granularity == 'week':
        points = 13
        step = timedelta(weeks=1)
    else:
        points = 12
        step = timedelta(days=30)

    cursor = start
    for _ in range(points):
        nxt = cursor + step
        labels.append(cursor.strftime('%d.%m' if granularity != 'hour' else '%H:00'))
        users_data.append(User.objects.filter(date_joined__gte=cursor, date_joined__lt=nxt).count())
        listings_data.append(
            Product.objects.filter(created_at__gte=cursor, created_at__lt=nxt).count()
            + Video.objects.filter(created_at__gte=cursor, created_at__lt=nxt).count()
        )
        payments_data.append(
            float(
                Order.objects.filter(
                    status='PAID', created_at__gte=cursor, created_at__lt=nxt
                ).aggregate(t=Sum('final_amount'))['t'] or 0
            )
        )
        orders_data.append(Order.objects.filter(created_at__gte=cursor, created_at__lt=nxt).count())
        cursor = nxt

    return {
        'labels': labels,
        'users': users_data,
        'listings': listings_data,
        'payments': payments_data,
        'orders': orders_data,
    }


def get_recent_activities(limit=20):
    items = []
    for u in User.objects.order_by('-date_joined')[:5]:
        items.append({
            'type': 'user',
            'icon': '👤',
            'text': f'Yangi foydalanuvchi: {u.username}',
            'time': u.date_joined.isoformat(),
            'ts': u.date_joined.timestamp(),
        })
    for p in Product.objects.select_related('seller').order_by('-created_at')[:5]:
        items.append({
            'type': 'listing',
            'icon': '📢',
            'text': f"Yangi e'lon: {p.title} — {p.seller.username}",
            'time': p.created_at.isoformat(),
            'ts': p.created_at.timestamp(),
        })
    for o in Order.objects.select_related('buyer').order_by('-created_at')[:5]:
        items.append({
            'type': 'order',
            'icon': '🛒',
            'text': f'Yangi buyurtma #{str(o.id)[:8]} — {o.buyer.username}',
            'time': o.created_at.isoformat(),
            'ts': o.created_at.timestamp(),
        })
    for tx in WalletTransaction.objects.select_related('wallet__user').order_by('-created_at')[:5]:
        items.append({
            'type': 'payment',
            'icon': '💳',
            'text': f"To'lov: {tx.wallet.user.username} — {tx.amount} UZS",
            'time': tx.created_at.isoformat(),
            'ts': tx.created_at.timestamp(),
        })
    for sub in UserSubscription.objects.select_related('user', 'plan').order_by('-start_date')[:3]:
        items.append({
            'type': 'premium',
            'icon': '⭐',
            'text': f'Premium: {sub.user.username} — {sub.plan.name}',
            'time': sub.start_date.isoformat(),
            'ts': sub.start_date.timestamp(),
        })
    for t in SupportTicket.objects.select_related('user').order_by('-created_at')[:3]:
        items.append({
            'type': 'ticket',
            'icon': '🎫',
            'text': f'Ticket #{t.id}: {t.subject}',
            'time': t.created_at.isoformat(),
            'ts': t.created_at.timestamp(),
        })
    items.sort(key=lambda x: x['ts'], reverse=True)
    return items[:limit]


def get_payment_stats():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    paid_qs = Order.objects.filter(status='PAID')
    return {
        'today_revenue': paid_qs.filter(created_at__gte=today_start).aggregate(t=Sum('final_amount'))['t'] or Decimal('0'),
        'monthly_revenue': paid_qs.filter(created_at__gte=month_start).aggregate(t=Sum('final_amount'))['t'] or Decimal('0'),
        'yearly_revenue': paid_qs.filter(created_at__gte=year_start).aggregate(t=Sum('final_amount'))['t'] or Decimal('0'),
        'pending_payments': WithdrawalRequest.objects.filter(status='PENDING').aggregate(t=Sum('amount'))['t'] or Decimal('0'),
        'pending_count': WithdrawalRequest.objects.filter(status='PENDING').count(),
    }


def get_admin_notifications(user):
    qs = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    return {
        'unread_count': Notification.objects.filter(user=user, is_read=False).count(),
        'items': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notif_type,
                'is_read': n.is_read,
                'url': n.target_url or '#',
                'time': n.created_at.isoformat(),
            }
            for n in qs
        ],
    }


def get_marketplace_analytics():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'sellers': User.objects.filter(role='SELLER').count(),
        'total_revenue': Order.objects.filter(status='PAID').aggregate(total=Sum('final_amount'))['total'] or 0,
        'monthly_revenue': Order.objects.filter(status='PAID', created_at__gte=month_start).aggregate(total=Sum('final_amount'))['total'] or 0,
        'today_revenue': Order.objects.filter(status='PAID', created_at__gte=today_start).aggregate(total=Sum('final_amount'))['total'] or 0,
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='NEW').count(),
    }


def listing_status(product=None, video=None):
    if product:
        if not product.is_active and not product.is_verified:
            return 'rejected'
        if not product.is_verified:
            return 'moderation'
        if product.is_active:
            return 'active'
        return 'expired'
    if video:
        if video.is_active:
            return 'active'
        return 'moderation'
    return 'active'
