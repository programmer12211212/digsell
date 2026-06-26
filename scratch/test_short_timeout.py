import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
# Configure logging to console to see our logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from apps.payments.services import HamyonPaymentService, HamyonClient
from apps.payments.models import HamyonPayment
from apps.users.models import User

# Ensure a test user exists
user = User.objects.first()
if not user:
    print("No user found in DB!")
    sys.exit(1)

print(f"Using user: {user.username}")

service = HamyonPaymentService()

try:
    print("\n--- Step 1: Creating a test payment ---")
    payment = service.create_payment(
        user=user,
        amount=1500,
        purpose=HamyonPayment.Purpose.WALLET_TOPUP,
        description="Verification payment"
    )
    print(f"Payment created successfully. ID: {payment.id}, External ID: {payment.external_id}")
    print(f"Card details: {payment.card}")
    print(f"Current status in DB: {payment.status}")
    
    print("\n--- Step 2: Processing payment status (Should timeout gracefully and return PENDING) ---")
    updated_payment = service.process_payment_status(payment)
    print(f"Status returned: {updated_payment.status}")
    print("Verification completed successfully!")
    
except Exception as e:
    import traceback
    traceback.print_exc()
