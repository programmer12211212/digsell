from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum

from apps.payments.models import Transaction, WithdrawalRequest
from apps.users.models import Wallet, WalletTransaction
from .permissions import staff_required
from .services import get_payment_stats, get_analytics_chart
from .utils import log_admin_action, broadcast_activity


@staff_required
def payment_dashboard(request):
    stats = get_payment_stats()
    chart = get_analytics_chart('30d')
    transactions = Transaction.objects.select_related('user').order_by('-created_at')[:50]
    withdrawals = WithdrawalRequest.objects.select_related('user').order_by('-created_at')[:20]
    return render(request, 'adminpanel/payments/dashboard.html', {
        'stats': stats,
        'chart_labels': chart['labels'],
        'chart_payments': chart['payments'],
        'transactions': transactions,
        'withdrawals': withdrawals,
    })


@require_POST
@staff_required
def approve_withdrawal(request, withdrawal_id):
    w = get_object_or_404(WithdrawalRequest, id=withdrawal_id, status=WithdrawalRequest.Status.PENDING)
    wallet, _ = Wallet.objects.get_or_create(user=w.user)
    if wallet.balance < w.amount:
        messages.error(request, "Foydalanuvchi balansida mablag' yetarli emas.")
        return redirect('adminpanel:payments')
    wallet.balance -= Decimal(str(w.amount))
    wallet.save(update_fields=['balance'])
    WalletTransaction.objects.create(
        wallet=wallet,
        amount=w.amount,
        tx_type='OUT',
        reason="Pul yechish tasdiqlandi (admin)",
    )
    w.status = WithdrawalRequest.Status.APPROVED
    w.save(update_fields=['status', 'updated_at'])
    log_admin_action(request.user, 'approve_withdrawal', 'WithdrawalRequest', withdrawal_id)
    broadcast_activity({'type': 'activity_item', 'icon': '💳', 'text': f"To'lov tasdiqlandi: {w.user.username}"})
    messages.success(request, "To'lov tasdiqlandi.")
    return redirect('adminpanel:payments')


@require_POST
@staff_required
def reject_withdrawal(request, withdrawal_id):
    w = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    w.status = WithdrawalRequest.Status.REJECTED
    w.save(update_fields=['status', 'updated_at'])
    log_admin_action(request.user, 'reject_withdrawal', 'WithdrawalRequest', withdrawal_id)
    messages.warning(request, "To'lov rad etildi.")
    return redirect('adminpanel:payments')
