from celery import shared_task

from .models import HamyonPayment
from .services import HamyonPaymentService


@shared_task
def check_single_hamyon_payment(payment_id):
    try:
        payment = HamyonPayment.objects.get(pk=payment_id)
    except HamyonPayment.DoesNotExist:
        return False

    service = HamyonPaymentService()
    service.process_payment_status(payment)
    return True


@shared_task
def check_pending_hamyon_payments():
    service = HamyonPaymentService()
    pending_payments = HamyonPayment.objects.filter(status=HamyonPayment.Status.PENDING)
    for payment in pending_payments:
        service.process_payment_status(payment)
    return len(pending_payments)
