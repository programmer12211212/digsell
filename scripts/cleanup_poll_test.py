import os
import sys
import pathlib

# Ensure project root is on sys.path so Django settings module can be imported
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.payments.models import HamyonPayment

User = get_user_model()

username = 'poll_test_user'
user = User.objects.filter(username=username).first()
if not user:
    print('No poll_test_user found')
    sys.exit(0)

# Delete HamyonPayments
hp_qs = HamyonPayment.objects.filter(user=user)
print('HamyonPayments to delete:', hp_qs.count())
hp_qs.delete()

# Delete TelegramPayment records linked to user's orders (if model exists)
try:
    from apps.telegram_services.models import TelegramPayment
    tp_qs = TelegramPayment.objects.filter(order__user=user)
    print('TelegramPayments to delete:', tp_qs.count())
    tp_qs.delete()
except Exception:
    print('TelegramPayment model not found or error listing; skipping')

print('Deleting user', user.username)
user.delete()
print('Cleanup complete')
