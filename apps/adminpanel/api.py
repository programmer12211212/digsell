from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from .permissions import is_admin_user


class IsPanelAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)

from apps.orders.models import Order
from apps.users.models import User
from .services import get_dashboard_stats, get_analytics_chart, get_recent_activities, get_admin_notifications


@api_view(['GET'])
@permission_classes([IsPanelAdmin])
def dashboard_data(request):
    stats = get_dashboard_stats()
    chart = get_analytics_chart(request.GET.get('range', '30d'))
    return Response({**stats, 'chart': chart})


@api_view(['GET'])
@permission_classes([IsPanelAdmin])
def analytics_data(request):
    range_key = request.GET.get('range', '30d')
    return Response(get_analytics_chart(range_key))


@api_view(['GET'])
@permission_classes([IsPanelAdmin])
def activity_feed(request):
    return Response({'items': get_recent_activities(limit=30)})


@api_view(['GET'])
@permission_classes([IsPanelAdmin])
def notifications_data(request):
    return Response(get_admin_notifications(request.user))


@api_view(['GET'])
@permission_classes([IsPanelAdmin])
def orders_list(request):
    status = request.GET.get('status')
    q = request.GET.get('q', '')
    qs = Order.objects.select_related('buyer').prefetch_related('items__product__seller').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(buyer__username__icontains=q)
    data = []
    for o in qs[:200]:
        item = o.items.select_related('product', 'product__seller').first()
        seller_name = item.product.seller.username if item and item.product else '—'
        product_title = item.product.title if item and item.product else '—'
        data.append({
            'id': str(o.id),
            'buyer': o.buyer.username,
            'seller': seller_name,
            'product': product_title,
            'amount': float(o.final_amount),
            'status': o.status,
            'status_display': o.get_status_display(),
            'created_at': o.created_at.isoformat(),
        })
    return Response({'results': data})
