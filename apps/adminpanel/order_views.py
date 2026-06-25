from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from apps.orders.models import Order
from apps.marketplace.views import _complete_order
from .permissions import staff_required
from .utils import log_admin_action


@staff_required
def order_list_admin(request):
    status_filter = request.GET.get('status')
    q = request.GET.get('q', '')
    orders = Order.objects.select_related('buyer').prefetch_related('items__product__seller').order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if q:
        orders = orders.filter(
            Q(buyer__username__icontains=q) | Q(id__icontains=q)
        )
    return render(request, 'adminpanel/orders/order_list.html', {
        'orders': orders, 'status_filter': status_filter, 'query': q,
    })


@require_POST
@staff_required
def order_bulk_action(request):
    action = request.POST.get('action')
    ids = request.POST.getlist('ids')
    count = 0
    for order in Order.objects.filter(id__in=ids).select_related('buyer'):
        if action == 'cancel':
            order.status = Order.Status.CANCELLED
            order.save(update_fields=['status', 'updated_at'])
            count += 1
        elif action == 'complete':
            if order.status == Order.Status.PAID:
                order.status = Order.Status.COMPLETED
                order.save(update_fields=['status', 'updated_at'])
            elif order.status in (Order.Status.NEW, Order.Status.PENDING):
                _complete_order(order, order.buyer)
                order.status = Order.Status.COMPLETED
                order.save(update_fields=['status', 'updated_at'])
            count += 1
    log_admin_action(request.user, f'bulk_order_{action}', 'Order', ','.join(ids))
    return JsonResponse({'success': True, 'count': count})


@staff_required
def order_detail_admin(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('buyer').prefetch_related('items__product'),
        id=order_id,
    )
    return render(request, 'adminpanel/orders/order_detail.html', {'order': order})


@staff_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    if new_status:
        old_status = order.status
        order.status = new_status
        order.save()
        if new_status == 'PAID' and old_status != 'PAID':
            _complete_order(order, order.buyer)
        messages.success(request, f"Buyurtma holati {order.get_status_display()} ga o'zgartirildi.")
    return redirect('adminpanel:order_detail', order_id=order.id)
