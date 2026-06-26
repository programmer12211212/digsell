from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.notifications.models import Notification
from apps.users.models import Wallet, WalletTransaction
from .models import UserCard, WithdrawalRequest, EscrowAccount, HamyonPayment
from .services import HamyonPaymentService
from .payment_ui import build_payment_status_payload, serialize_hamyon_payment_for_create
from .wallet_services import (
    MIN_WALLET_TOPUP,
    WalletPurchaseService,
    WalletService,
    WalletTopupService,
)


def _wants_json(request):
    accept = request.headers.get('Accept', '')
    return (
        'application/json' in accept
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.POST.get('format') == 'json'
    )


def _serialize_hamyon_payment(payment):
    return serialize_hamyon_payment_for_create(payment)


class WalletView(LoginRequiredMixin, TemplateView):
    template_name = "payments/wallet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        escrow, _ = EscrowAccount.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        context['escrow'] = escrow
        context['transactions'] = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:20]
        context['cards'] = UserCard.objects.filter(user=self.request.user).order_by('-created_at')
        context['withdrawals'] = WithdrawalRequest.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:20]

        context['hamyon_payments'] = HamyonPayment.objects.filter(
            user=self.request.user,
            purpose=HamyonPayment.Purpose.WALLET_TOPUP,
        ).order_by('-created_at')[:20]

        context['min_topup_amount'] = int(MIN_WALLET_TOPUP)
        
        return context


@login_required
@require_POST
def create_hamyon_payment(request):
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        purpose = request.POST.get('purpose', HamyonPayment.Purpose.WALLET_TOPUP)
        purpose_reference = request.POST.get('purpose_reference') or None
        description = request.POST.get('description', '').strip()
        metadata = {}

        if purpose == HamyonPayment.Purpose.WALLET_TOPUP:
            payment = WalletTopupService.create_auto_topup(request.user, amount)
        else:
            min_amount = Decimal('1000')
            if amount < min_amount:
                raise ValueError(f"Minimal summa {min_amount:,.0f} so'm bo'lishi kerak.")

            if purpose == HamyonPayment.Purpose.MARKETPLACE_ORDER and purpose_reference:
                from apps.orders.models import Order
                order = Order.objects.filter(id=purpose_reference, buyer=request.user).first()
                if not order:
                    raise ValueError("Buyurtma topilmadi yoki bu buyurtmaga ruxsat yo'q.")
                metadata['order_id'] = str(order.id)
                description = description or f"Marketplace buyurtma #{order.id}"

            service = HamyonPaymentService()
            payment = service.create_payment(
                request.user,
                amount,
                purpose=purpose,
                purpose_reference=purpose_reference,
                description=description,
                metadata=metadata,
            )

        if _wants_json(request):
            return JsonResponse({
                'success': True,
                'payment': _serialize_hamyon_payment(payment),
            })

        if purpose == HamyonPayment.Purpose.MARKETPLACE_ORDER:
            messages.success(
                request,
                f"Hamyon orqali buyurtma to'lovi yaratildi. To'lov ID: {payment.external_id}. Statusni tekshiring va buyurtma avtomatik yakunlanadi."
            )
            return redirect('marketplace:payment_page', order_id=purpose_reference)

        messages.success(
            request,
            f"Hamyon to'lov yaratildi. To'lov ID: {payment.external_id}. Pulni to'lash uchun kartani pastdagi ro'yxatda ko'rishingiz mumkin."
        )
    except (InvalidOperation, ValueError) as exc:
        if _wants_json(request):
            return JsonResponse({'success': False, 'message': str(exc)}, status=400)
        messages.error(request, str(exc))
        return redirect(request.META.get('HTTP_REFERER', 'payments:wallet'))
    except Exception:
        if _wants_json(request):
            return JsonResponse({'success': False, 'message': "Hamyon API bilan bog'lanishda xatolik."}, status=500)
        messages.error(request, "Hamyon API bilan bog'lanishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
        return redirect(request.META.get('HTTP_REFERER', 'payments:wallet'))
    return redirect('payments:wallet')


@login_required
def hamyon_payment_status(request, payment_id):
    payment = get_object_or_404(HamyonPayment, pk=payment_id, user=request.user)

    if request.GET.get('refresh'):
        service = HamyonPaymentService()
        try:
            payment = service.process_payment_status(payment)
            payment.refresh_from_db()
        except Exception:
            return JsonResponse({'success': False, 'message': 'Hamyon holatini tekshirishda xato yuz berdi.'}, status=500)

    return JsonResponse(build_payment_status_payload(payment))


@login_required
@require_POST
def cancel_hamyon_payment(request, payment_id):
    payment = get_object_or_404(HamyonPayment, pk=payment_id, user=request.user)
    if not payment.can_cancel():
        return JsonResponse({'success': False, 'message': 'Ushbu to‘lovni bekor qilish mumkin emas.'}, status=400)

    payment.status = HamyonPayment.Status.CANCELLED
    payment.save(update_fields=['status', 'updated_at'])
    Notification.objects.create(
        user=request.user,
        notif_type=Notification.Type.WALLET_PAYMENT_CANCELLED,
        title="Hamyon to'lov bekor qilindi",
        message=f"Hamyon to'lovingiz {payment.amount} so'm uchun bekor qilindi.",
        target_url='/payments/wallet/'
    )
    return JsonResponse({'success': True, 'message': 'To‘lov muvaffaqiyatli bekor qilindi.'})


@login_required
def withdraw_funds(request):
    if request.method == 'POST':
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            card_id = request.POST.get('card_id')
            if amount > wallet.balance:
                messages.error(request, "Balans yetarli emas.")
            elif amount < 10000:
                messages.error(request, "Minimal yechish summasi 10,000 so'm.")
            else:
                card = None
                if card_id:
                    card = UserCard.objects.filter(id=card_id, user=request.user).first()
                WithdrawalRequest.objects.create(
                    user=request.user,
                    amount=amount,
                    card=card,
                    status=WithdrawalRequest.Status.PENDING,
                )
                messages.success(request, "Pul yechish so'rovi yuborildi. Admin tasdiqlashini kuting.")
        except (InvalidOperation, ValueError):
            messages.error(request, "Noto'g'ri summa.")
    return redirect('payments:wallet')


@login_required
@require_POST
def add_card(request):
    card_number = (request.POST.get('card_number') or '').strip()
    card_holder = (request.POST.get('card_holder') or '').strip()
    expiry_date = (request.POST.get('expiry_date') or '').strip()

    if not card_number or not card_holder or not expiry_date:
        messages.error(request, "Iltimos, barcha maydonlarni to'ldiring.")
        return redirect('payments:wallet')

    normalized = card_number.replace(' ', '')
    if len(normalized) < 12 or len(normalized) > 20 or not normalized.isdigit():
        messages.error(request, "Karta raqami noto'g'ri ko'rsatilgan.")
        return redirect('payments:wallet')

    parts = expiry_date.split('/')
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        messages.error(request, "Karta muddati MM/YY formatida bo'lishi kerak.")
        return redirect('payments:wallet')

    try:
        is_primary = not UserCard.objects.filter(user=request.user).exists()
        if is_primary:
            UserCard.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        UserCard.objects.create(
            user=request.user,
            card_number=normalized,
            card_holder=card_holder.upper(),
            expiry_date=expiry_date,
            is_primary=is_primary,
        )
        messages.success(request, "Karta muvaffaqiyatli ulandi.")
    except Exception:
        messages.error(request, "Karta saqlashda xatolik yuz berdi.")

    return redirect('payments:wallet')


@login_required
def debug_hamyon_payment(request):
    """Debug endpoint: check latest payment status from Hamyon API"""
    try:
        latest_payment = HamyonPayment.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        if not latest_payment:
            return JsonResponse({'error': 'No payments found'}, status=404)
        
        service = HamyonPaymentService()
        
        # Get latest status from Hamyon
        hamyon_response = service.client.get_payment_status(latest_payment.external_id, timeout=5)
        
        # Process the payment
        service.process_payment_status(latest_payment)
        latest_payment.refresh_from_db()
        
        return JsonResponse({
            'payment_id': str(latest_payment.id),
            'external_id': latest_payment.external_id,
            'db_status': latest_payment.status,
            'db_processed': latest_payment.processed,
            'hamyon_response': hamyon_response,
            'processed': latest_payment.processed,
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': type(e).__name__,
        }, status=500)


@login_required
def test_mark_payment_success(request, payment_id):
    """TEST ONLY: Manually mark a payment as successful for testing"""
    payment = get_object_or_404(HamyonPayment, pk=payment_id, user=request.user)
    
    if request.method == 'POST':
        payment.status = HamyonPayment.Status.SUCCESS
        payment.processed = False
        payment.save(update_fields=['status', 'processed'])
        
        # Trigger payment processing
        service = HamyonPaymentService()
        if payment.purpose == HamyonPayment.Purpose.WALLET_TOPUP:
            payment.apply_balance()
        else:
            processed = service.process_related_payment(payment)
            if processed:
                payment.processed = True
                payment.paid_at = timezone.now()
                payment.save(update_fields=['processed', 'paid_at'])
        
        return JsonResponse({
            'status': 'success',
            'message': f'Payment {payment_id} marked as SUCCESS',
            'payment_status': payment.status,
            'processed': payment.processed,
        })
    
    return JsonResponse({
        'error': 'Only POST requests allowed',
        'payment_id': payment_id,
        'current_status': payment.status,
    }, status=405)


@login_required
def wallet_balance_check(request):
    """Check if wallet has enough balance for a purchase amount."""
    try:
        required = Decimal(request.GET.get('amount', '0'))
    except (InvalidOperation, ValueError):
        return JsonResponse({'success': False, 'message': 'Noto\'g\'ri summa.'}, status=400)

    result = WalletService.check_balance(request.user, required)
    payload = result.to_dict()
    payload['success'] = result.sufficient
    return JsonResponse(payload)


@login_required
@require_POST
def wallet_auto_topup(request):
    """Create automatic wallet top-up with unique payment amount."""
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        payment = WalletTopupService.create_auto_topup(request.user, amount)
        return JsonResponse({
            'success': True,
            'payment': serialize_hamyon_payment_for_create(payment),
        })
    except (InvalidOperation, ValueError) as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'message': "Hamyon API bilan bog'lanishda xatolik."}, status=500)
