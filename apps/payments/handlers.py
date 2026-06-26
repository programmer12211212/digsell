"""Module-specific Hamyon payment success handlers.

Each purchasable flow only implements process_success() and optional delivery context.
Generic polling, status checks, and Hamyon API calls stay in HamyonPaymentService.
"""
import logging

from django.db import transaction

from .models import HamyonPayment

logger = logging.getLogger(__name__)


class BasePaymentHandler:
    purpose = None

    def process_success(self, payment: HamyonPayment) -> bool:
        raise NotImplementedError

    def get_delivery_context(self, payment: HamyonPayment) -> dict:
        return {
            'delivery_status': 'completed' if payment.processed else 'pending',
            'is_complete': bool(payment.processed),
            'redirect_url': None,
        }


class WalletTopupHandler(BasePaymentHandler):
    purpose = HamyonPayment.Purpose.WALLET_TOPUP

    def process_success(self, payment: HamyonPayment) -> bool:
        from apps.payments.wallet_services import WalletTopupService

        if payment.processed:
            return True

        credited = WalletTopupService.credit_from_payment(payment)
        payment.refresh_from_db()
        return payment.processed or credited > 0

    def get_delivery_context(self, payment: HamyonPayment) -> dict:
        return {
            'delivery_status': 'completed' if payment.processed else 'processing',
            'is_complete': bool(payment.processed),
            'redirect_url': '/payments/wallet/',
        }


class MarketplaceOrderHandler(BasePaymentHandler):
    purpose = HamyonPayment.Purpose.MARKETPLACE_ORDER

    def process_success(self, payment: HamyonPayment) -> bool:
        from apps.orders.models import Order

        if not payment.purpose_reference:
            return False

        order = Order.objects.filter(id=payment.purpose_reference, buyer=payment.user).first()
        if not order:
            logger.warning('Marketplace order %s not found for payment %s', payment.purpose_reference, payment.external_id)
            return False

        if order.status not in (Order.Status.PAID, Order.Status.COMPLETED):
            order.payment_method = 'hamyon'
            order.transaction_id = payment.external_id
            order.status = Order.Status.PAID
            order.save(update_fields=['payment_method', 'transaction_id', 'status'])

        return True

    def get_delivery_context(self, payment: HamyonPayment) -> dict:
        from apps.orders.models import Order

        order = None
        if payment.purpose_reference:
            order = Order.objects.filter(id=payment.purpose_reference, buyer=payment.user).first()

        order_status = str(getattr(order, 'status', '') or '').lower()
        is_complete = order_status in {'paid', 'completed'} if order else bool(payment.processed)

        return {
            'delivery_status': order_status or 'pending',
            'is_complete': is_complete,
            'redirect_url': f'/marketplace/order/pay/{order.id}/' if order else None,
        }


class TelegramOrderHandler(BasePaymentHandler):
    purpose = HamyonPayment.Purpose.TELEGRAM_ORDER

    def process_success(self, payment: HamyonPayment) -> bool:
        from apps.telegram_services.delivery_pipeline_trace import get_trace, log_order_context
        from apps.telegram_services.models import TelegramOrder
        from apps.telegram_services.services import TelegramOrderService

        if not payment.purpose_reference:
            return False

        get_trace().mark_reached('process_related_payment')

        with transaction.atomic():
            try:
                telegram_order = TelegramOrder.objects.select_for_update().get(
                    id=payment.purpose_reference,
                    user=payment.user,
                )
            except TelegramOrder.DoesNotExist:
                get_trace().mark_stopped('process_related_payment', f'TelegramOrder {payment.purpose_reference} not found')
                return False

            log_order_context(telegram_order, prefix='process_related_payment')

            if telegram_order.status == 'waiting_payment':
                confirmed = TelegramOrderService.confirm_payment(
                    telegram_order,
                    admin_user=payment.user,
                    note=f'Hamyon orqali avtomatik tasdiqlash (HamyonID: {payment.external_id})',
                    payment_method='hamyon',
                    transaction_id=payment.external_id,
                )
                if not confirmed:
                    get_trace().mark_stopped('process_related_payment', 'confirm_payment returned False')
                get_trace().log_summary()
                return bool(confirmed)

            if telegram_order.status in ['paid', 'processing', 'completed']:
                return True

        return False

    def get_delivery_context(self, payment: HamyonPayment) -> dict:
        from apps.telegram_services.models import TelegramOrder

        order = None
        if payment.purpose_reference:
            order = TelegramOrder.objects.filter(id=payment.purpose_reference, user=payment.user).first()

        order_status = str(getattr(order, 'status', '') or '').lower()
        is_complete = order_status in {'completed', 'delivered'}

        return {
            'delivery_status': order_status or 'pending',
            'is_complete': is_complete,
            'redirect_url': f'/telegram-services/orders/{order.id}/' if order else None,
        }


class SubscriptionHandler(BasePaymentHandler):
    """Placeholder for future subscription purchases via Hamyon."""

    purpose = 'SUBSCRIPTION'

    def process_success(self, payment: HamyonPayment) -> bool:
        logger.warning('Subscription Hamyon handler not implemented for payment %s', payment.external_id)
        return False


HANDLERS = {
    HamyonPayment.Purpose.WALLET_TOPUP: WalletTopupHandler(),
    HamyonPayment.Purpose.MARKETPLACE_ORDER: MarketplaceOrderHandler(),
    HamyonPayment.Purpose.TELEGRAM_ORDER: TelegramOrderHandler(),
}


def get_payment_handler(purpose: str) -> BasePaymentHandler | None:
    return HANDLERS.get(purpose)
