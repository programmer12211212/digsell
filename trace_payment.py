import os
import django
import logging
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService

# Force logging to stdout
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logging.getLogger('apps').addHandler(handler)
logging.getLogger('apps').setLevel(logging.INFO)

p = HamyonPayment.objects.all().order_by('-created_at').first()
if p:
    print(f"DEBUG: Found payment {p.id}, status={p.status}")
    service = HamyonPaymentService()
    service.process_payment_status(p)
else:
    print("DEBUG: No payments found")
