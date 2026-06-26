import os
import django
import logging
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.telegram_services.models import TelegramOrder, TelegramOrderLog
from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService
from apps.telegram_services.services import TelegramOrderService

# Force logging to stdout
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s | %(name)s | %(message)s')
handler.setFormatter(formatter)

# Add to relevant loggers
loggers = ['apps.payments', 'apps.telegram_services', 'apps.telegram_services.services']
for lname in loggers:
    l = logging.getLogger(lname)
    l.addHandler(handler)
    l.setLevel(logging.INFO)

print("--- DELIVERY AUDIT START ---")

# 1. Find orders stuck in 'paid' but not processed
stuck_orders = TelegramOrder.objects.filter(status='paid')
print(f"Found {stuck_orders.count()} orders in 'paid' status")

for order in stuck_orders:
    print(f"\nAUDITING ORDER: {order.unique_code} (ID: {order.id})")
    print(f"Product: {order.product.name} (Category: {order.product.category.name})")
    
    # Check logs for this order
    logs = TelegramOrderLog.objects.filter(order=order).order_by('created_at')
    print("History:")
    for l in logs:
        print(f"  {l.created_at} | {l.action} | {l.message}")

    # Check Hamyon Payment
    payment = HamyonPayment.objects.filter(purpose_reference=str(order.id)).first()
    if payment:
        print(f"Hamyon Payment: {payment.id} Status: {payment.status} Processed: {payment.processed}")
    else:
        print("No Hamyon Payment found in DB for this reference.")

    # Try to re-trigger delivery
    print("\nAttempting to re-trigger delivery via TelegramOrderService.process_delivery(order)...")
    success = TelegramOrderService.process_delivery(order)
    print(f"Result: {success}")

print("\n--- DELIVERY AUDIT END ---")
