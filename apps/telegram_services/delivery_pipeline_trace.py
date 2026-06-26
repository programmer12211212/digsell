"""Delivery pipeline execution trace — instrumentation only."""
import logging
import traceback

logger = logging.getLogger('delivery.pipeline')

_active_trace = None


class _NoOpTrace:
    def mark_reached(self, step_name):
        pass

    def mark_stopped(self, location, reason):
        pass

    def mark_fragment_response(self, http_status, raw_response, json_response):
        pass

    def log_summary(self):
        pass


class DeliveryPipelineTrace:
    def __init__(self, payment_external_id=''):
        self.payment_external_id = payment_external_id
        self.process_payment_status_reached = False
        self.process_related_payment_reached = False
        self.confirm_payment_reached = False
        self.process_delivery_reached = False
        self.send_stars_reached = False
        self.fragment_api_called = False
        self.stop_location = None
        self.stop_reason = None
        self.fragment_http_status = None
        self.fragment_raw_response = None
        self.fragment_json_response = None

    def mark_reached(self, step_name):
        setattr(self, f'{step_name}_reached', True)

    def mark_stopped(self, location, reason):
        if self.stop_location is None:
            self.stop_location = location
            self.stop_reason = reason

    def mark_fragment_response(self, http_status, raw_response, json_response):
        self.fragment_api_called = True
        self.fragment_http_status = http_status
        self.fragment_raw_response = raw_response
        self.fragment_json_response = json_response

    def log_summary(self):
        lines = ['=== DELIVERY PIPELINE EXECUTION TRACE ===']

        def _mark(reached):
            return '[OK]' if reached else '[--]'

        def _stop():
            return '[STOP]'

        lines.append(f"{_mark(self.process_payment_status_reached)} process_payment_status reached")
        lines.append(f"{_mark(self.process_related_payment_reached)} process_related_payment reached")
        lines.append(f"{_mark(self.confirm_payment_reached)} confirm_payment reached")
        lines.append(f"{_mark(self.process_delivery_reached)} process_delivery reached")
        lines.append(f"{_mark(self.send_stars_reached)} send_stars reached")
        lines.append(f"{_mark(self.fragment_api_called)} Fragment API called")

        if self.fragment_api_called:
            lines.append(f"  HTTP {self.fragment_http_status}")
            lines.append(f"  Raw response: {self.fragment_raw_response}")
            lines.append(f"  JSON response: {self.fragment_json_response}")
        elif self.stop_location and self.stop_reason:
            if self.process_delivery_reached and not self.send_stars_reached:
                lines.append('')
                lines.append('[OK] process_delivery reached')
                lines.append(f'{_stop()} send_stars stopped')
            elif self.confirm_payment_reached and not self.process_delivery_reached:
                lines.append('')
                lines.append('[OK] confirm_payment reached')
                lines.append(f'{_stop()} process_delivery stopped')
            elif self.process_related_payment_reached and not self.confirm_payment_reached:
                lines.append('')
                lines.append('[OK] process_related_payment reached')
                lines.append(f'{_stop()} confirm_payment stopped')
            elif self.process_payment_status_reached and not self.process_related_payment_reached:
                lines.append('')
                lines.append('[OK] process_payment_status reached')
                lines.append(f'{_stop()} process_related_payment stopped')

            lines.append('Reason:')
            lines.append(f"  {self.stop_reason}")
            lines.append(f"  Stopped at: {self.stop_location}")

        lines.append('=== END DELIVERY PIPELINE TRACE ===')
        logger.info('\n'.join(lines))


def start_trace(payment_external_id=''):
    global _active_trace
    _active_trace = DeliveryPipelineTrace(payment_external_id=payment_external_id)
    return _active_trace


def get_trace():
    return _active_trace or _NoOpTrace()


def log_order_context(order, prefix=''):
    product = getattr(order, 'product', None)
    provider = getattr(product, 'provider', None) if product else None
    if provider is None and product:
        from .models import TelegramProvider
        provider = TelegramProvider.objects.filter(is_active=True).first()

    category = getattr(getattr(product, 'category', None), 'name', None) if product else None
    stars_quantity = None
    if product:
        stars_quantity = order.custom_quantity or getattr(product, 'quantity', None)

    logger.info(
        "%sorder.id=%s | order.status=%s | product.id=%s | product.category=%s | "
        "product.auto_delivery=%s | provider=%s | provider_enabled=%s | "
        "telegram_username=%s | telegram_user_id=%s | recipient=%s | "
        "stars_quantity=%s | delivery_attempts=%s",
        f"{prefix} " if prefix else '',
        getattr(order, 'id', None),
        getattr(order, 'status', None),
        getattr(product, 'id', None) if product else None,
        category,
        getattr(product, 'auto_delivery', None) if product else None,
        getattr(provider, 'name', None) if provider else None,
        getattr(provider, 'is_active', None) if provider else None,
        getattr(order, 'telegram_username', None),
        getattr(order, 'telegram_user_id', None),
        getattr(order, 'telegram_username', None),
        stars_quantity,
        getattr(order, 'delivery_attempts', None),
    )


def log_exception(location, exc):
    logger.error("EXCEPTION at %s: %s: %s", location, type(exc).__name__, exc)
    logger.error(traceback.format_exc())
