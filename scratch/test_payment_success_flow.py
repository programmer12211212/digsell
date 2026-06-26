import os
import sys
import django
from decimal import Decimal
import uuid
import random
from unittest.mock import patch

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from apps.users.models import User
from apps.telegram_services.models import TelegramOrder, TelegramProduct
from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService, HamyonClient

def run_test():
    print("=== STARTING END-TO-END SIMULATED SUCCESSFUL PAYMENT TEST ===")
    
    # 1. Retrieve User and Product
    user = User.objects.get(username="uchqunbekc")
    product = TelegramProduct.objects.filter(status='active').first()
    
    # 2. Create TelegramOrder
    unique_amount = product.price_uzs + Decimal(str(random.randint(1, 99)))
    unique_code = f"TX{uuid.uuid4().hex[:6].upper()}"
    
    order = TelegramOrder.objects.create(
        user=user,
        product=product,
        telegram_username="uchqunbekc",
        status='waiting_payment',
        base_price=product.price_uzs,
        unique_amount=unique_amount,
        unique_code=unique_code
    )
    print(f"Created TelegramOrder: ID={order.id}, Code={order.unique_code}, status={order.status}")
    
    # 3. Create HamyonPayment (Mocking the external API call)
    with patch.object(HamyonClient, 'create_payment') as mock_create:
        payment_id = f"pay_{uuid.uuid4().hex[:8]}"
        mock_create.return_value = {
            'payment_id': payment_id,
            'amount': str(order.unique_amount),
            'card': '9860120178594715',
            'message': 'Mock creation success'
        }
        
        service = HamyonPaymentService()
        payment = service.create_payment(
            user=user,
            amount=order.unique_amount,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id),
            description=f"Telegram order {order.unique_code}"
        )
    print(f"Created HamyonPayment: ID={payment.id}, External ID={payment.external_id}, status={payment.status}")
    
    # 4. Create related TelegramPayment (created by the view)
    from apps.telegram_services.models import TelegramPayment as TPayment
    t_pay, _ = TPayment.objects.update_or_create(
        order=order,
        defaults={
            'amount': order.unique_amount,
            'currency': 'UZS',
            'payment_method': 'hamyon',
            'payment_details': {'external_id': payment.external_id, 'card': payment.card}
        }
    )
    print(f"Initial TelegramPayment status: {t_pay.payment_status}")
    
    print("\n--- Simulating Hamyon API returning PENDING ---")
    with patch.object(HamyonClient, 'get_payment_status') as mock_status:
        # Mock pending status
        mock_status.return_value = {
            'payment_id': payment.external_id,
            'amount': str(payment.amount),
            'status': 'pending',
            'card': payment.card
        }
        
        # Process status
        payment = service.process_payment_status(payment)
        order.refresh_from_db()
        t_pay.refresh_from_db()
        print(f"After pending check -> HamyonPayment status: {payment.status}")
        print(f"After pending check -> TelegramOrder status: {order.status}")
        print(f"After pending check -> TelegramPayment status: {t_pay.payment_status}")
        
    print("\n--- Simulating Hamyon API returning PAID (Success) ---")
    with patch.object(HamyonClient, 'get_payment_status') as mock_status:
        # Mock successful status
        mock_status.return_value = {
            'payment_id': payment.external_id,
            'amount': str(payment.amount),
            'status': 'paid',
            'card': payment.card,
            'paid_at': timezone_now_iso()
        }
        
        # Process status
        payment = service.process_payment_status(payment)
        order.refresh_from_db()
        t_pay.refresh_from_db()
        print(f"After paid check -> HamyonPayment status: {payment.status} | Processed: {payment.processed}")
        print(f"After paid check -> TelegramOrder status: {order.status} | Payment Method: {order.payment_method}")
        print(f"After paid check -> TelegramPayment status: {t_pay.payment_status}")
        
    # Clean up
    order.delete()
    payment.delete()
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")

def timezone_now_iso():
    from django.utils import timezone
    return timezone.now().isoformat()

if __name__ == '__main__':
    run_test()
