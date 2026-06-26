"""Central wallet operations for marketplace purchases and top-ups."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Optional

from django.db import transaction
from django.utils import timezone

from apps.users.models import Wallet, WalletTransaction

from .models import CompanyCard, HamyonPayment
from .unique_amount import UniqueAmountGenerator

logger = logging.getLogger(__name__)

MIN_WALLET_TOPUP = Decimal('5000')


class InsufficientBalanceError(Exception):
    def __init__(self, balance: Decimal, required: Decimal):
        self.balance = balance
        self.required = required
        super().__init__(f"Balans yetarli emas: {balance} < {required}")


@dataclass
class BalanceCheckResult:
    sufficient: bool
    balance: Decimal
    required: Decimal

    def to_dict(self) -> dict:
        if self.sufficient:
            return {'success': True}
        return {
            'success': False,
            'code': 'INSUFFICIENT_BALANCE',
            'wallet_balance': str(self.balance),
            'required_amount': str(self.required),
            'message': "Hisobingizda mablag' yetarli emas.",
        }


class WalletTransactionService:
    @staticmethod
    def create(
        wallet: Wallet,
        *,
        amount: Decimal,
        tx_type: str,
        operation_type: str,
        balance_before: Decimal,
        balance_after: Decimal,
        description: str = '',
        reference: str = '',
        reason: str = '',
    ) -> WalletTransaction:
        return WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            tx_type=tx_type,
            reason=reason or description,
            operation_type=operation_type,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference=reference,
        )


class WalletService:
    @staticmethod
    def get_wallet(user, lock: bool = False) -> Wallet:
        wallet, _ = Wallet.objects.get_or_create(user=user)
        if lock:
            return Wallet.objects.select_for_update().get(pk=wallet.pk)
        return wallet

    @staticmethod
    def get_balance(user) -> Decimal:
        wallet = WalletService.get_wallet(user)
        return wallet.balance

    @staticmethod
    def check_balance(user, required_amount: Decimal) -> BalanceCheckResult:
        balance = WalletService.get_balance(user)
        return BalanceCheckResult(
            sufficient=balance >= required_amount,
            balance=balance,
            required=required_amount,
        )

    @staticmethod
    def credit(
        user,
        amount: Decimal,
        *,
        operation_type: str = WalletTransaction.OperationType.TOPUP,
        description: str = '',
        reference: str = '',
    ) -> Wallet:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Kiritiladigan summa musbat bo'lishi kerak.")

        with transaction.atomic():
            wallet = WalletService.get_wallet(user, lock=True)
            balance_before = wallet.balance
            balance_after = balance_before + amount
            wallet.balance = balance_after
            wallet.save(update_fields=['balance', 'updated_at'])

            WalletTransactionService.create(
                wallet,
                amount=amount,
                tx_type='IN',
                operation_type=operation_type,
                balance_before=balance_before,
                balance_after=balance_after,
                description=description,
                reference=reference,
                reason=description,
            )
        return wallet

    @staticmethod
    def debit(
        user,
        amount: Decimal,
        *,
        operation_type: str = WalletTransaction.OperationType.PURCHASE,
        description: str = '',
        reference: str = '',
    ) -> Wallet:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Yechiladigan summa musbat bo'lishi kerak.")

        with transaction.atomic():
            wallet = WalletService.get_wallet(user, lock=True)
            if wallet.balance < amount:
                raise InsufficientBalanceError(wallet.balance, amount)

            balance_before = wallet.balance
            balance_after = balance_before - amount
            wallet.balance = balance_after
            wallet.save(update_fields=['balance', 'updated_at'])

            WalletTransactionService.create(
                wallet,
                amount=amount,
                tx_type='OUT',
                operation_type=operation_type,
                balance_before=balance_before,
                balance_after=balance_after,
                description=description,
                reference=reference,
                reason=description,
            )
        return wallet


class WalletPurchaseService:
    @staticmethod
    def purchase(
        user,
        amount: Decimal,
        deliver: Callable[[], None],
        *,
        description: str,
        reference: str = '',
    ) -> dict:
        amount = Decimal(str(amount))
        try:
            with transaction.atomic():
                WalletService.debit(
                    user,
                    amount,
                    operation_type=WalletTransaction.OperationType.PURCHASE,
                    description=description,
                    reference=reference,
                )
                deliver()
            return {'success': True}
        except InsufficientBalanceError as exc:
            return BalanceCheckResult(
                sufficient=False,
                balance=exc.balance,
                required=exc.required,
            ).to_dict()

    @staticmethod
    def purchase_marketplace_order(user, order, complete_order_fn) -> dict:
        amount = order.final_amount or order.total_amount
        return WalletPurchaseService.purchase(
            user,
            amount,
            deliver=lambda: complete_order_fn(order, user),
            description=f"Marketplace buyurtma #{order.id}",
            reference=str(order.id),
        )


class WalletTopupService:
    @staticmethod
    def validate_requested_amount(amount: Decimal) -> Decimal:
        amount = Decimal(str(amount))
        if amount < MIN_WALLET_TOPUP:
            raise ValueError(f"Minimal to'ldirish summasi {MIN_WALLET_TOPUP:,.0f} so'm.")
        return amount

    @staticmethod
    def get_active_company_card() -> Optional[CompanyCard]:
        return CompanyCard.objects.filter(is_active=True).order_by('id').first()

    @staticmethod
    def create_auto_topup(user, requested_amount: Decimal):
        """Create a pending Hamyon wallet top-up with a unique payment amount."""
        from .services import HamyonPaymentService

        requested_amount = WalletTopupService.validate_requested_amount(requested_amount)

        with transaction.atomic():
            existing = (
                HamyonPayment.objects.select_for_update()
                .filter(
                    user=user,
                    purpose=HamyonPayment.Purpose.WALLET_TOPUP,
                    status=HamyonPayment.Status.PENDING,
                )
                .order_by('-created_at')
                .first()
            )
            if existing and not existing.is_expired:
                return existing

            actual_amount, variance, payment_code = UniqueAmountGenerator.generate_wallet_topup_amount(
                requested_amount
            )

            service = HamyonPaymentService()
            payment = service.create_payment(
                user,
                actual_amount,
                purpose=HamyonPayment.Purpose.WALLET_TOPUP,
                description=f"Balans to'ldirish ({payment_code})",
                metadata={
                    'requested_amount': str(requested_amount),
                    'variance': variance,
                    'payment_code': payment_code,
                },
                requested_amount=requested_amount,
                payment_code=payment_code,
            )
        return payment

    @staticmethod
    def credit_from_payment(payment: HamyonPayment) -> Decimal:
        """Credit wallet from a successful top-up payment. Returns credited amount."""
        if payment.processed or payment.status != HamyonPayment.Status.SUCCESS:
            return Decimal('0')

        if payment.purpose != HamyonPayment.Purpose.WALLET_TOPUP:
            return Decimal('0')

        reference = payment.payment_code or payment.external_id
        if WalletTransaction.objects.filter(
            wallet__user=payment.user,
            reference=reference,
            operation_type=WalletTransaction.OperationType.TOPUP,
        ).exists():
            return Decimal('0')

        credit_amount = payment.requested_amount
        if credit_amount is None and payment.metadata:
            credit_amount = payment.metadata.get('requested_amount')
        if credit_amount is not None:
            credit_amount = Decimal(str(credit_amount))
        else:
            credit_amount = payment.amount

        WalletService.credit(
            payment.user,
            credit_amount,
            operation_type=WalletTransaction.OperationType.TOPUP,
            description=f"Hamyon avtomatik to'ldirish #{payment.external_id}",
            reference=reference,
        )

        from apps.notifications.models import Notification
        from apps.core.utils import format_uzs

        Notification.objects.create(
            user=payment.user,
            notif_type=Notification.Type.WALLET_TOPUP,
            title='Balans to\'ldirildi',
            message=f'Sizning hamyoningiz {format_uzs(credit_amount)} miqdorida to\'ldirildi.',
            target_url='/payments/wallet/',
        )
        return credit_amount
