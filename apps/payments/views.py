from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.users.models import Wallet, WalletTransaction
from .models import UserCard, WithdrawalRequest, EscrowAccount


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
        
        # Load deposit requests
        from .models import DepositRequest
        context['deposits'] = DepositRequest.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:20]
        
        return context


@login_required
@require_POST
def topup_wallet(request):
    try:
        amount = Decimal(request.POST.get('amount', '0'))
        receipt_image = request.FILES.get('receipt_image')
        
        if amount < 1000:
            messages.error(request, "Minimal to'ldirish summasi 1,000 so'm.")
            return redirect('payments:wallet')
            
        if not receipt_image:
            messages.error(request, "To'lov cheki (rasm) yuklanishi shart.")
            return redirect('payments:wallet')
            
        from .models import DepositRequest
        DepositRequest.objects.create(
            user=request.user,
            amount=amount,
            receipt_image=receipt_image,
            status=DepositRequest.Status.PENDING
        )
        messages.success(request, "Balans to'ldirish so'rovi yuborildi. Admin tasdiqlagach hisobingizga pul qo'shiladi.")
    except (InvalidOperation, ValueError):
        messages.error(request, "Noto'g'ri summa kiritildi.")
    return redirect('payments:wallet')


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
