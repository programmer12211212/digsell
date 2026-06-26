import json
import logging
from decimal import Decimal
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Coupon, CouponValidationAttempt, CouponUsage, HamyonPayment

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


logger = logging.getLogger(__name__)


class HamyonClient:
    base_url = getattr(settings, 'HAMYON_API_URL', 'https://hamyon-api.uz')
    shop_id = getattr(settings, 'HAMYON_SHOP_ID', None)
    shop_key = getattr(settings, 'HAMYON_SHOP_KEY', None)
    timeout = getattr(settings, 'HAMYON_API_TIMEOUT', 15)

    def __init__(self):
        if not self.shop_id or not self.shop_key:
            raise ValueError('HAMYON_SHOP_ID and HAMYON_SHOP_KEY must be configured in settings.')

    def _request(self, path, data=None, method='GET', timeout=None):
        url = self.base_url.rstrip('/') + '/' + path.lstrip('/')
        payload = None
        headers = {'Accept': 'application/json'}
        if method == 'GET' and data:
            url = url + '?' + urlencode(data)
        elif data:
            payload = urlencode(data).encode()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        request = Request(url, data=payload, headers=headers, method=method)

        t = timeout if timeout is not None else self.timeout
        logger.info(f"Hamyon API Request: {method} {url} with payload {data} (timeout={t})")

        try:
            with urlopen(request, timeout=t) as response:
                status_code = response.status
                raw = response.read().decode('utf-8')
                logger.info(f"Hamyon API Response: status={status_code}, body={raw}")
                logger.info("Hamyon raw response: %s", raw)
                return json.loads(raw or '{}')
        except HTTPError as exc:
            body = exc.read().decode('utf-8')
            logger.error(f"Hamyon API HTTP Error: status={exc.code}, body={body}")
            try:
                error_data = json.loads(body or '{}')
                raise RuntimeError(error_data.get('message') or str(error_data) or str(exc))
            except json.JSONDecodeError:
                raise RuntimeError(body or str(exc))
        except URLError as exc:
            logger.error(f"Hamyon API URL Error: reason={exc.reason}")
            raise RuntimeError(f'Hamyon API connection failed: {exc.reason}')

    def create_payment(self, amount):
        amount_int = int(Decimal(amount))
        data = {
            'shop_id': self.shop_id,
            'shop_key': self.shop_key,
            'amount': amount_int,
        }
        return self._request('payment/create', data=data, method='POST')

    def get_payment_status(self, payment_id, timeout=None):
        return self._request(
            f'merchant/{payment_id}/json',
            data=None,
            method='GET',
            timeout=timeout,
        )


class HamyonPaymentService:
    def __init__(self, client=None):
        self.client = client or HamyonClient()

    def create_payment(
        self,
        user,
        amount,
        purpose=None,
        purpose_reference=None,
        description='',
        metadata=None,
        requested_amount=None,
        payment_code=None,
    ):
        if purpose is None:
            purpose = HamyonPayment.Purpose.WALLET_TOPUP

        min_amount = Decimal('5000') if purpose == HamyonPayment.Purpose.WALLET_TOPUP else Decimal('1000')
        if Decimal(amount) < min_amount:
            raise ValueError(f"Minimal summa {min_amount:,.0f} so'm bo'lishi kerak.")

        if purpose not in HamyonPayment.Purpose.values:
            raise ValueError("Noto'g'ri to'lov maqsadi.")

        response = self.client.create_payment(amount)
        external_id = response.get('payment_id') or response.get('id')
        if not external_id:
            raise RuntimeError('Hamyon API dan payment_id qaytmadi.')

        card_info = response.get('card')
        expires_at = timezone.now() + timedelta(minutes=5)

        fee_amount = Decimal('0')
        if requested_amount is not None:
            fee_amount = Decimal(amount) - Decimal(requested_amount)
            if fee_amount < 0:
                raise ValueError('Unique amount cannot be less than requested amount.')

        payment = HamyonPayment.objects.create(
            user=user,
            external_id=external_id,
            amount=Decimal(amount),
            requested_amount=Decimal(requested_amount) if requested_amount is not None else None,
            fee_amount=fee_amount,
            payment_code=payment_code,
            purpose=purpose,
            purpose_reference=purpose_reference,
            description=description or f"Hamyon to'lovi ({purpose})",
            metadata=metadata or {},
            card=card_info,
            status=HamyonPayment.Status.PENDING,
            external_data=response,
            expires_at=expires_at,
        )

        try:
            # Check if Redis broker is online before queuing Celery task to avoid blocking the thread
            from django.conf import settings
            broker_url = getattr(settings, 'CELERY_BROKER_URL', '')
            redis_active = False
            if broker_url.startswith('redis://') or broker_url.startswith('rediss://'):
                import socket
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(broker_url)
                    host = parsed.hostname or 'localhost'
                    port = parsed.port or 6379
                    s = socket.create_connection((host, port), timeout=0.1)
                    s.close()
                    redis_active = True
                except Exception:
                    redis_active = False

            if redis_active:
                from .tasks import check_single_hamyon_payment
                check_single_hamyon_payment.apply_async(args=[payment.id], countdown=30)
            else:
                logger.info("Celery Redis broker is offline; skipped direct task queueing (polling command is active).")
        except Exception:
            pass

        return payment

    def process_payment_status(self, payment):
        from apps.telegram_services.delivery_pipeline_trace import start_trace, get_trace

        logger.info("ENTER process_payment_status")
        logger.info(
            "payment.external_id=%s | payment.status=%s | payment.processed=%s | "
            "payment.purpose=%s | payment.purpose_reference=%s | payment.user_id=%s",
            payment.external_id,
            payment.status,
            payment.processed,
            payment.purpose,
            payment.purpose_reference,
            payment.user_id,
        )
        trace = start_trace(payment_external_id=payment.external_id)
        trace.mark_reached('process_payment_status')

        payment.refresh_from_db()

        if payment.status == HamyonPayment.Status.SUCCESS and payment.processed:
            trace.mark_stopped('process_payment_status', 'payment already SUCCESS and processed=True')
            logger.info("RETURN because payment already SUCCESS and processed=True")
            get_trace().log_summary()
            return payment

        import socket
        import urllib.error

        try:
            logger.info(f"STEP 1a: Calling Hamyon API get_payment_status for {payment.external_id}")
            response = self.client.get_payment_status(
                payment.external_id,
                timeout=2.0
            )

            logger.info(f"STEP 1b: Hamyon API Response for {payment.external_id}: {response}")

        except (socket.timeout, TimeoutError, urllib.error.URLError) as exc:
            is_timeout = False
            if isinstance(exc, (socket.timeout, TimeoutError)):
                is_timeout = True
            elif isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, (socket.timeout, TimeoutError)):
                is_timeout = True

            if is_timeout:
                if payment.status != HamyonPayment.Status.PENDING:
                    get_trace().mark_stopped(
                        'process_payment_status',
                        f'Hamyon status check timed out and payment.status={payment.status} is not PENDING',
                    )
                    logger.info("RETURN because Hamyon status check timed out and payment.status=%s is not PENDING", payment.status)
                    get_trace().log_summary()
                    return payment
                payment.status = HamyonPayment.Status.PENDING
                payment.save(update_fields=['status'])
                get_trace().mark_stopped('process_payment_status', 'Hamyon status check timed out; saved PENDING')
                logger.info("RETURN because Hamyon status check timed out; saved PENDING")
                get_trace().log_summary()
                return payment
            else:
                logger.error(f"STEP 1-ERROR: Hamyon network error: {type(exc).__name__}: {exc}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        except Exception as exc:
            logger.error(f"STEP 1-ERROR: Hamyon unexpected error: {exc}")
            raise
        
        logger.info(f"STEP 1c: Normalizing remote status from response")
        def normalize_status(value):
            if value is None:
                return ''
            if isinstance(value, bool):
                return 'success' if value else 'failed'
            if isinstance(value, (int, float)):
                return str(int(value))
            return str(value).strip().lower().replace(' ', '_').replace('-', '_').replace('.', '')

        remote_status = ''
        for key in ('status', 'state', 'payment_status', 'transaction_status', 'result', 'payment_state', 'status_code', 'code'):
            value = response.get(key)
            if value is not None:
                remote_status = normalize_status(value)
                logger.info(f"Hamyon: extracted status from key '{key}': {value} -> normalized: {remote_status}")
                break

        if not remote_status and isinstance(response.get('data'), dict):
            nested_response = response['data']
            for key in ('status', 'state', 'payment_status', 'transaction_status', 'result', 'payment_state', 'status_code', 'code'):
                value = nested_response.get(key)
                if value is not None:
                    remote_status = normalize_status(value)
                    logger.info(f"Hamyon: extracted status from nested data['{key}']: {value} -> normalized: {remote_status}")
                    break

        if not remote_status:
            if response.get('success') is True or response.get('paid') is True or response.get('is_paid') is True:
                remote_status = 'success'
                logger.info(f"Hamyon: detected success from boolean flags")
            elif response.get('success') is False:
                remote_status = 'failed'
                logger.info(f"Hamyon: detected failed from success=False")

        logger.info(f"STEP 1d: Final extracted status='{remote_status}' for payment_id={payment.external_id}")

        previous_status = payment.status

        status_mapping = {
            'paid': HamyonPayment.Status.SUCCESS,
            'success': HamyonPayment.Status.SUCCESS,
            'successful': HamyonPayment.Status.SUCCESS,
            'succeeded': HamyonPayment.Status.SUCCESS,
            'completed': HamyonPayment.Status.SUCCESS,
            'complete': HamyonPayment.Status.SUCCESS,
            'confirmed': HamyonPayment.Status.SUCCESS,
            'approved': HamyonPayment.Status.SUCCESS,
            'done': HamyonPayment.Status.SUCCESS,
            'processed': HamyonPayment.Status.SUCCESS,
            'cancel': HamyonPayment.Status.CANCELLED,
            'canceled': HamyonPayment.Status.CANCELLED,
            'cancelled': HamyonPayment.Status.CANCELLED,
            'declined': HamyonPayment.Status.FAILED,
            'rejected': HamyonPayment.Status.FAILED,
            'expired': HamyonPayment.Status.EXPIRED,
            'timeout': HamyonPayment.Status.EXPIRED,
            'timed_out': HamyonPayment.Status.EXPIRED,
            'failed': HamyonPayment.Status.FAILED,
            'fail': HamyonPayment.Status.FAILED,
            'error': HamyonPayment.Status.FAILED,
            'pending': HamyonPayment.Status.PENDING,
            'waiting': HamyonPayment.Status.PENDING,
            'created': HamyonPayment.Status.PENDING,
            'processing': HamyonPayment.Status.PENDING,
            'in_progress': HamyonPayment.Status.PENDING,
            'in_process': HamyonPayment.Status.PENDING,
            'new': HamyonPayment.Status.PENDING,
        }

        if remote_status not in status_mapping:
            get_trace().mark_stopped('process_payment_status', f'unknown remote status: {remote_status!r}')
            logger.info("RETURN because unknown remote Hamyon status=%r", remote_status)
            payment.external_data = response
            payment.card = response.get('card') or payment.card
            payment.save(update_fields=['external_data', 'card'])
            get_trace().log_summary()
            return payment

        new_status = status_mapping[remote_status]
        logger.info(f"STEP 1e: Mapped remote_status='{remote_status}' -> new_status={new_status}")
        
        if new_status == HamyonPayment.Status.PENDING and payment.is_final:
            get_trace().mark_stopped(
                'process_payment_status',
                f'new_status=PENDING but payment.is_final=True (current status={payment.status})',
            )
            logger.info("RETURN because new_status=PENDING but payment.is_final=True (current status=%s)", payment.status)
            payment.external_data = response
            payment.card = response.get('card') or payment.card
            payment.save(update_fields=['external_data', 'card'])
            get_trace().log_summary()
            return payment

        payment.status = new_status
        logger.info(f"STEP 1f: Updating payment {payment.external_id} status: {previous_status} -> {payment.status}")

        payment.external_data = response
        payment.card = response.get('card') or payment.card
        payment.save(update_fields=['status', 'external_data', 'card'])

        if payment.status == HamyonPayment.Status.SUCCESS and not payment.processed:
            from .handlers import get_payment_handler

            handler = get_payment_handler(payment.purpose)
            if handler:
                logger.info(f"STEP 2: Calling payment handler for purpose={payment.purpose}")
                try:
                    processed = handler.process_success(payment)
                    payment.refresh_from_db()
                    logger.info(f"STEP 2-END: handler.process_success() returned {processed}")
                    if processed and not payment.processed:
                        logger.info(f"STEP 2-SUCCESS: Marking payment {payment.external_id} as processed.")
                        payment.processed = True
                        payment.paid_at = timezone.now()
                        payment.save(update_fields=['processed', 'paid_at'])
                    elif not processed:
                        logger.warning(f"STEP 2-FAILED: handler returned False for payment {payment.external_id}")
                except Exception as e:
                    logger.error(f"STEP 2-EXCEPTION: payment handler failed with {type(e).__name__}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"STEP 2-SKIP: No handler for purpose={payment.purpose}")
        elif payment.status in {
            HamyonPayment.Status.CANCELLED,
            HamyonPayment.Status.EXPIRED,
            HamyonPayment.Status.FAILED,
        } and previous_status != payment.status and not payment.processed:
            logger.info(f"STEP 1L: Notifying failure for status {payment.status}")
            self._notify_failure(payment)

        logger.info("RETURN process_payment_status completed for payment.external_id=%s", payment.external_id)
        get_trace().log_summary()
        return payment


    def process_related_payment(self, payment):
        """Backward-compatible alias for module success handlers."""
        from .handlers import get_payment_handler

        handler = get_payment_handler(payment.purpose)
        if not handler:
            logger.info("RETURN because purpose '%s' not handled here", payment.purpose)
            return False
        return handler.process_success(payment)

    def _notify_failure(self, payment):
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=payment.user,
            notif_type=Notification.Type.WALLET_PAYMENT_FAILED,
            title="Hamyon to'lov holati",
            message=f"Hamyon to'lovingiz {payment.get_status_display()} holatiga o'tdi.",
            target_url='/payments/wallet/'
        )
