import os
import sys
import django
from decimal import Decimal

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from django.test import Client
from apps.users.models import User
from apps.telegram_services.models import TelegramOrder, TelegramProduct
from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService

# Get a user and a product
user = User.objects.first()
product = TelegramProduct.objects.filter(status='active').first()

if not user or not product:
    print("Database lacks necessary test users or active products!")
    sys.exit(1)

print(f"Test User: {user.username}")
print(f"Test Product: {product.name} (Price: {product.price_uzs})")

# Create a test TelegramOrder
import uuid
order = TelegramOrder.objects.create(
    user=user,
    product=product,
    telegram_username="test_buyer",
    status='waiting_payment',
    base_price=product.price_uzs,
    unique_amount=product.price_uzs + Decimal('15'),
    unique_code=f"TST{uuid.uuid4().hex[:6].upper()}"
)
print(f"Created TelegramOrder with ID {order.id} and unique_amount {order.unique_amount}")

# Create HamyonPayment
service = HamyonPaymentService()
payment = service.create_payment(
    user=user,
    amount=order.unique_amount,
    purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
    purpose_reference=str(order.id),
    description=f"Telegram order {order.unique_code} checkout"
)
print(f"Created HamyonPayment: external_id={payment.external_id}, card={payment.card}")

# Setup Django Test Client
client = Client()
client.force_login(user)

print("\n--- Testing GET /telegram-services/orders/<order_id>/check-hamyon-status/ ---")
import time
start = time.time()
# Set HTTP_HOST to a allowed host
response = client.get(f"/telegram-services/orders/{order.id}/check-hamyon-status/", HTTP_HOST="127.0.0.1")
duration = time.time() - start

print(f"Response status code: {response.status_code}")
print(f"Response JSON: {response.json()}")
print(f"Polling completed in {duration:.2f} seconds")

# Clean up
order.delete()
payment.delete()
print("\nTest finished!")
