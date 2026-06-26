"""Unified Hamyon payment UI status mapping for frontend polling."""

from .handlers import get_payment_handler
from .models import HamyonPayment


class PaymentUIStatus:
    WAITING = 'WAITING'
    PROCESSING = 'PROCESSING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
    EXPIRED = 'EXPIRED'


def build_payment_status_payload(payment: HamyonPayment) -> dict:
    handler = get_payment_handler(payment.purpose)
    delivery_context = handler.get_delivery_context(payment) if handler else {
        'delivery_status': 'pending',
        'is_complete': bool(payment.processed),
        'redirect_url': None,
    }

    ui_status = _resolve_ui_status(payment, delivery_context)
    status_value = str(payment.status or '').upper()
    delivery_status = str(delivery_context.get('delivery_status') or '').lower()
    is_complete = bool(delivery_context.get('is_complete'))

    message = _build_message(payment, ui_status, delivery_context)

    return {
        'success': True,
        'ui_status': ui_status,
        'payment_status': status_value,
        'processed': payment.processed,
        'delivery_status': delivery_status,
        'is_complete': is_complete,
        'message': message,
        'payment_id': payment.id,
        'external_id': payment.external_id,
        'fee_amount': str(payment.fee_amount),
        'unique_amount': str(payment.unique_amount),
        'requested_amount': str(payment.requested_amount) if payment.requested_amount else None,
        'card': payment.card or '',
        'purpose': payment.purpose,
        'amount': str(payment.amount),
        'expires_at': payment.expires_at.isoformat() if payment.expires_at else None,
        'expires_at_epoch': int(payment.expires_at.timestamp()) if payment.expires_at else None,
        'redirect_url': delivery_context.get('redirect_url'),
    }


def _resolve_ui_status(payment: HamyonPayment, delivery_context: dict) -> str:
    status = payment.status

    if status == HamyonPayment.Status.PENDING:
        if payment.is_expired:
            return PaymentUIStatus.EXPIRED
        return PaymentUIStatus.WAITING

    if status == HamyonPayment.Status.FAILED:
        return PaymentUIStatus.FAILED
    if status == HamyonPayment.Status.CANCELLED:
        return PaymentUIStatus.CANCELLED
    if status == HamyonPayment.Status.EXPIRED:
        return PaymentUIStatus.EXPIRED

    if status == HamyonPayment.Status.SUCCESS:
        if delivery_context.get('is_complete'):
            return PaymentUIStatus.SUCCESS
        return PaymentUIStatus.PROCESSING

    return PaymentUIStatus.WAITING


def serialize_hamyon_payment_for_create(payment: HamyonPayment) -> dict:
    """Normalized create-payment payload for the shared frontend controller."""
    from .wallet_services import WalletTopupService

    payload = build_payment_status_payload(payment)
    payload['payment_pk'] = payment.id
    payload['requested_amount'] = str(payment.requested_amount) if payment.requested_amount else None
    payload['unique_amount'] = str(payment.unique_amount)
    payload['actual_amount'] = str(payment.amount)
    payload['fee_amount'] = str(payment.fee_amount)
    payload['payment_code'] = payment.payment_code or ''
    payload['payment_id'] = payment.payment_id

    company_card = WalletTopupService.get_active_company_card()
    if company_card:
        payload['card_holder'] = company_card.card_holder
        payload['card_name'] = company_card.card_name
    else:
        payload['card_holder'] = ''
        payload['card_name'] = ''

    return payload


def _build_message(payment: HamyonPayment, ui_status: str, delivery_context: dict) -> str:
    if ui_status == PaymentUIStatus.WAITING:
        return "To'lov kutilmoqda..."
    if ui_status == PaymentUIStatus.PROCESSING:
        return "To'lov tasdiqlandi. Yetkazish jarayoni davom etmoqda..."
    if ui_status == PaymentUIStatus.SUCCESS:
        return "To'lov muvaffaqiyatli yakunlandi."
    if ui_status == PaymentUIStatus.CANCELLED:
        return "To'lov bekor qilindi."
    if ui_status == PaymentUIStatus.EXPIRED:
        return "To'lov muddati tugadi."
    if ui_status == PaymentUIStatus.FAILED:
        return "To'lov amalga oshmadi."
    return payment.get_status_display()
