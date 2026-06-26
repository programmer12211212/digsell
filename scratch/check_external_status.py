import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.services import HamyonClient

client = HamyonClient()

payment_ids = ["53c71e33813b", "1a390ec1d65b", "e232b4bbdd8c", "080046237a10"]

for pid in payment_ids:
    print(f"\nQuerying Hamyon API for payment ID: {pid}...")
    try:
        res = client.get_payment_status(pid, timeout=5.0)
        print("Response:", res)
    except Exception as e:
        print("Error:", e)
