import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService
from django.utils import timezone

service = HamyonPaymentService()

print("=== HamyonPayments in DB ===")
payments = HamyonPayment.objects.all().order_by('-created_at')[:20]
if not payments.exists():
    print("No Hamyon payments found in database.")
    sys.exit(0)

for p in payments:
    print(f"ID: {p.id} | External ID: {p.external_id} | Amount: {p.amount} | Status: {p.status} | Processed: {p.processed} | Created: {p.created_at}")

print("\n=== Running status checks on all PENDING payments ===")
pending_payments = HamyonPayment.objects.filter(status=HamyonPayment.Status.PENDING)
for p in pending_payments:
    print(f"\nChecking status for Payment ID {p.id} (External ID: {p.external_id})...")
    try:
        updated = service.process_payment_status(p)
        print(f"Result -> Status: {updated.status} | Processed: {updated.processed}")
        if updated.status == HamyonPayment.Status.SUCCESS:
            print(f"SUCCESS: Payment {p.id} was processed successfully!")
            # Print related order details if any
            if p.purpose_reference:
                print(f"Purpose: {p.purpose} | Reference ID: {p.purpose_reference}")
                if p.purpose == HamyonPayment.Purpose.TELEGRAM_ORDER:
                    from apps.telegram_services.models import TelegramOrder, TelegramPayment
                    try:
                        order = TelegramOrder.objects.get(id=p.purpose_reference)
                        print(f"TelegramOrder ID: {order.id} | Status: {order.status} | Payment Method: {order.payment_method}")
                        # Check TelegramPayment
                        pay_record = getattr(order, 'payment', None)
                        if pay_record:
                            print(f"TelegramPayment ID: {pay_record.id} | Status: {pay_record.payment_status}")
                    except TelegramOrder.DoesNotExist:
                        print("TelegramOrder not found.")
    except Exception as e:
        print(f"Error checking status: {e}")

print("\n=== Finished checking pending payments ===")
