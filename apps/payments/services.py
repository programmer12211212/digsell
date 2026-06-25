import json
from decimal import Decimal
from datetime import timedelta
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Coupon, CouponValidationAttempt, CouponUsage

COUPON_SALT = 'payments.coupon_order_token'
COUPON_MAX_AGE = 3600
MAX_FAILED_ATTEMPTS = 6
MAX_FAILED_IP_ATTEMPTS = 12
FAILED_ATTEMPT_WINDOW = timedelta(minutes=15)


def get_coupon_order_token(user, order):
    payload = {
        'order_id': order.id,
        'user_id': user.id,
    }
    return signing.dumps(payload, salt=COUPON_SALT)


def verify_coupon_order_token(token, user, order_id):
    try:
        payload = signing.loads(token, salt=COUPON_SALT, max_age=COUPON_MAX_AGE)
    except signing.SignatureExpired:
        raise ValidationError("Promo token muddati tugagan. Sahifani yangilang va qayta urinib ko'ring.")
    except signing.BadSignature:
        raise ValidationError("Noto'g'ri promo token.")

    if payload.get('user_id') != user.id or payload.get('order_id') != order_id:
        raise ValidationError("Promo token ma'lumotlari noto'g'ri.")
    return payload


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def is_coupon_rate_limited(request, user, order, code):
    ip_address = get_client_ip(request)
    window_start = timezone.now() - FAILED_ATTEMPT_WINDOW
    user_attempts = CouponValidationAttempt.objects.filter(
        user=user,
        order=order,
        code=code.upper(),
        is_success=False,
        created_at__gte=window_start,
    ).count()
    ip_attempts = CouponValidationAttempt.objects.filter(
        ip_address=ip_address,
        code=code.upper(),
        is_success=False,
        created_at__gte=window_start,
    ).count()
    return user_attempts >= MAX_FAILED_ATTEMPTS or ip_attempts >= MAX_FAILED_IP_ATTEMPTS


def log_coupon_attempt(order, user, code, success, reason='', request=None, ip_address=None):
    coupon = Coupon.objects.filter(code=code.upper()).first()
    if ip_address is None and request is not None:
        ip_address = get_client_ip(request)

    CouponValidationAttempt.objects.create(
        coupon=coupon,
        user=user,
        order=order,
        code=code.upper(),
        ip_address=ip_address or 'unknown',
        is_success=success,
        reason=reason,
    )


def validate_coupon_for_order(order, coupon_code, request):
    code = (coupon_code or '').strip().upper()
    if not code:
        raise ValidationError("Iltimos, promo kodni kiriting.")

    if is_coupon_rate_limited(request, request.user, order, code):
        raise ValidationError("Ko'p xato urinishlar bo'ldi. Iltimos, 15 daqiqa kuting.")

    coupon = Coupon.objects.filter(code=code).first()
    if not coupon:
        log_coupon_attempt(order, request.user, code, False, 'Kod topilmadi', request=request)
        raise ValidationError("Bunday promo kod topilmadi.")

    try:
        coupon.is_valid_for_order(order, request.user)
    except ValidationError as exc:
        log_coupon_attempt(order, request.user, code, False, str(exc), request=request)
        raise

    calculation = coupon.calculate_discount(order)
    log_coupon_attempt(order, request.user, code, True, 'Kod tasdiqlandi', request=request)

    return {
        'coupon': coupon,
        'discount_amount': calculation['discount_amount'],
        'final_amount': calculation['final_amount'],
        'commission': calculation['commission'],
        'message': 'Promo kod muvaffaqiyatli qo‘llandi.',
    }


def apply_coupon_to_order(order, coupon, discount_amount, final_amount, commission):
    order.coupon = coupon
    order.coupon_code = coupon.code
    order.discount_amount = discount_amount
    order.final_amount = final_amount
    order.commission = commission
    order.save(update_fields=['coupon', 'coupon_code', 'discount_amount', 'final_amount', 'commission'])


def register_coupon_usage(order, user, amount_saved, request=None, ip_address=None):
    if order.coupon:
        order.coupon.register_usage(
            user=user,
            order=order,
            amount_saved=amount_saved,
            ip_address=ip_address or (get_client_ip(request) if request is not None else 'unknown'),
        )
