import os
import sys
import django
from decimal import Decimal
import uuid
import random
import time

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
# Configure standard logging to output to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from django.utils import timezone
from apps.users.models import User
from apps.telegram_services.models import TelegramOrder, TelegramProduct
from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService, HamyonClient

def run_e2e_test():
    print("="*60)
    print("STARTING REAL END-TO-END HAMYON PAYMENT TEST")
    print("="*60)
    
    # 1. Retrieve User and Product
    user = User.objects.get(username="uchqunbekc")
    product = TelegramProduct.objects.get(id="80f5d5fe-143e-4ae4-bc95-911a9b63e66e") # 50 Stars (1500 UZS)
    
    # 2. Generate a unique code and random unique amount
    variance = random.randint(1, 99)
    unique_amount = product.price_uzs + Decimal(str(variance))
    unique_code = f"TX{uuid.uuid4().hex[:6].upper()}"
    
    # 3. Create TelegramOrder
    order = TelegramOrder.objects.create(
        user=user,
        product=product,
        telegram_username="uchqunbekc",
        status='waiting_payment',
        base_price=product.price_uzs,
        unique_amount=unique_amount,
        unique_code=unique_code
    )
    
    # Create related TelegramPayment
    from apps.telegram_services.models import TelegramPayment as TPayment
    t_pay, _ = TPayment.objects.update_or_create(
        order=order,
        defaults={
            'amount': order.unique_amount,
            'currency': 'UZS',
            'payment_method': 'hamyon',
            'payment_details': {}
        }
    )
    
    print("\n--- DATABASE VALUES BEFORE PAYMENT ---")
    print(f"TelegramOrder ID: {order.id}")
    print(f"TelegramOrder Unique Code: {order.unique_code}")
    print(f"TelegramOrder status: {order.status}")
    print(f"TelegramPayment status: {t_pay.payment_status}")
    
    # 4. Create HamyonPayment (sends HTTP request to Hamyon API)
    print("\n--- STEP 1: SENDING PAYMENT CREATE REQUEST TO HAMYON API ---")
    service = HamyonPaymentService()
    
    try:
        payment = service.create_payment(
            user=user,
            amount=order.unique_amount,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id),
            description=f"Telegram order {order.unique_code}"
        )
    except Exception as e:
        print(f"Failed to create payment: {e}")
        order.delete()
        t_pay.delete()
        sys.exit(1)
        
    t_pay.payment_details = {'external_id': payment.external_id, 'card': payment.card}
    t_pay.save(update_fields=['payment_details'])
    
    print("\n--- DATABASE VALUES AFTER CREATION ---")
    print(f"HamyonPayment ID: {payment.id}")
    print(f"HamyonPayment External ID (payment_id): {payment.external_id}")
    print(f"HamyonPayment Card: {payment.card}")
    print(f"HamyonPayment Amount: {payment.amount}")
    print(f"HamyonPayment status: {payment.status}")
    
    print("\n" + "="*50)
    print("ACTION REQUIRED FROM USER:")
    print(f"Please transfer exactly {payment.amount} UZS to card: {payment.card}")
    print("Once you complete the transfer, the polling loop below will detect it!")
    print("This polling loop will run for 3 minutes (180 seconds).")
    print("="*50 + "\n")
    
    # 5. Polling loop
    poll_duration = 180  # seconds
    interval = 5        # seconds
    elapsed = 0
    success = False
    
    print("--- STARTING 5-SECOND POLLING LOOP ---")
    while elapsed < poll_duration:
        time.sleep(interval)
        elapsed += interval
        print(f"\n[{elapsed}s / {poll_duration}s] Polling Hamyon status for external ID: {payment.external_id}...")
        
        try:
            # Query Hamyon API and update status
            payment = service.process_payment_status(payment)
            print(f"Hamyon status: {payment.status} | Processed: {payment.processed}")
            
            if payment.status == HamyonPayment.Status.SUCCESS:
                print("Payment successfully completed and verified!")
                success = True
                break
            elif payment.status in [HamyonPayment.Status.CANCELLED, HamyonPayment.Status.EXPIRED, HamyonPayment.Status.FAILED]:
                print(f"Payment ended with final status: {payment.status}")
                break
        except Exception as e:
            print(f"Polling error: {e}")
            
    # 6. Refresh and print DB status
    order.refresh_from_db()
    t_pay.refresh_from_db()
    
    print("\n" + "="*50)
    print("DATABASE VALUES AFTER TEST")
    print("="*50)
    print(f"HamyonPayment status: {payment.status} | Processed: {payment.processed}")
    print(f"TelegramOrder status: {order.status} | Payment Method: {order.payment_method}")
    print(f"TelegramPayment status: {t_pay.payment_status}")
    print("="*50)
    
    if success:
        print("\nCONFIRMATION: End-to-end automatic payment confirmation works successfully!")
    else:
        print("\nWARNING: Payment was not completed within the polling duration.")
        
    print("="*60)

if __name__ == "__main__":
    run_e2e_test()
