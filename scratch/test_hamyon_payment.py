import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.services import HamyonClient

client = HamyonClient()
print("Base URL:", client.base_url)
print("Shop ID:", client.shop_id)
print("Shop KEY:", client.shop_key)

try:
    print("Creating a test payment for 2000 UZS...")
    res = client.create_payment(2000)
    print("Create Payment Response:", res)
    
    payment_id = res.get('payment_id') or res.get('id')
    if payment_id:
        print(f"Checking payment status for {payment_id}...")
        status_res = client.get_payment_status(payment_id)
        print("Status Response:", status_res)
    else:
        print("No payment ID returned")
except Exception as e:
    import traceback
    traceback.print_exc()
