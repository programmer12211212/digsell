import os
import sys
import django
from decimal import Decimal
import uuid
import random

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.telegram_services.models import TelegramOrder, TelegramProduct
from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService

# Retrieve the superuser
user = User.objects.get(username="uchqunbekc")
# Retrieve the 50 Telegram Stars product
product = TelegramProduct.objects.get(id="80f5d5fe-143e-4ae4-bc95-911a9b63e66e")

# Generate unique amount using unique amount logic
# (Let's generate unique amount adding between 1 and 99 UZS)
variance = random.randint(1, 99)
unique_amount = product.price_uzs + Decimal(str(variance))
unique_code = f"TX{uuid.uuid4().hex[:6].upper()}"

# Create TelegramOrder
order = TelegramOrder.objects.create(
    user=user,
    product=product,
    telegram_username="uchqunbekc",
    status='waiting_payment',
    base_price=product.price_uzs,
    unique_amount=unique_amount,
    unique_code=unique_code
)

# Create HamyonPayment
service = HamyonPaymentService()
payment = service.create_payment(
    user=user,
    amount=unique_amount,
    purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
    purpose_reference=str(order.id),
    description=f"Telegram order {order.unique_code} checkout"
)

# Output with clean encoding safe print
print("\n" + "="*50)
print("REAL TEST PAYMENT INITIATED")
print("="*50)
print(f"TelegramOrder ID: {order.id}")
print(f"TelegramOrder Unique Code: {order.unique_code}")
print(f"HamyonPayment ID: {payment.id}")
print(f"HamyonPayment External ID: {payment.external_id}")
print(f"HamyonPayment Card: {payment.card}")
print(f"HamyonPayment Amount UZS: {payment.amount}")
print(f"Status in DB before payment: HamyonPayment={payment.status}, TelegramOrder={order.status}")
print("="*50)
print("INSTRUCTIONS FOR USER:")
print(f"Please transfer exactly {payment.amount} UZS to card: {payment.card}")
print("Once the transfer is completed, please let me know. The background poller is running and will confirm it!")
print("="*50 + "\n")
