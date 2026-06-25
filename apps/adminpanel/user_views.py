from django.shortcuts import render, get_object_or_404
from .permissions import staff_required
from django.http import JsonResponse
from django.db.models import Q, Count, Exists, OuterRef
from apps.subscriptions.models import UserSubscription
from django.views.decorators.http import require_POST

from apps.users.models import User, Wallet, WalletTransaction
from apps.subscriptions.models import SubscriptionPlan
from .utils import log_admin_action, broadcast_activity


@staff_required
def user_list_view(request):
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    users = User.objects.select_related('wallet').annotate(
        orders_count=Count('orders', distinct=True),
        listings_count=Count('seller_videos', distinct=True),
        has_premium=Exists(
            UserSubscription.objects.filter(user=OuterRef('pk'), is_active=True)
        ),
    )
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )
    if role:
        users = users.filter(role=role)
    users = users.order_by('-date_joined')
    plans = SubscriptionPlan.objects.all()
    return render(request, 'adminpanel/users/user_list.html', {
        'users': users, 'query': q, 'role': role, 'plans': plans,
    })


@require_POST
@staff_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    action = 'unban' if user.is_active else 'ban'
    log_admin_action(request.user, action, 'User', user_id)
    broadcast_activity({'type': 'activity_item', 'icon': '🛡', 'text': f'{action.upper()}: {user.username}'})
    status_label = "Faol" if user.is_active else "Bloklangan"
    return JsonResponse({'success': True, 'is_active': user.is_active, 'label': status_label})


@require_POST
@staff_required
def adjust_balance(request, user_id):
    user = get_object_or_404(User, id=user_id)
    amount = float(request.POST.get('amount', 0))
    action = request.POST.get('action')

    wallet, _ = Wallet.objects.get_or_create(user=user)
    if action in ('add', 'subtract'):
        if action == 'add':
            wallet.balance += amount
            reason = "Admin tomonidan qo'shildi"
        else:
            wallet.balance -= amount
            reason = "Admin tomonidan ayirildi"
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        tx_type='IN' if action == 'add' else 'OUT',
        reason=reason,
    )
    return JsonResponse({'success': True, 'balance': float(wallet.balance)})


@require_POST
@staff_required
def verify_seller(request, user_id):
    user = get_object_or_404(User, id=user_id)
    action = request.POST.get('action')
    if action == 'approve':
        user.is_verified = True
        user.is_seller_approved = True
        user.role = User.Role.SELLER
        user.save()
        return JsonResponse({'success': True, 'message': "Seller tasdiqlandi"})
    user.is_verified = False
    user.is_seller_approved = False
    user.save()
    return JsonResponse({'success': True, 'message': "Seller rad etildi"})
