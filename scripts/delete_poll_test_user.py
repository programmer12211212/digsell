import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.payments.models import HamyonPayment
from apps.telegram_services.models import TelegramPayment

User = get_user_model()

def run():
    user = User.objects.filter(username='poll_test_user').first()
    if not user:
        print('No poll_test_user found')
        return

    hp_qs = HamyonPayment.objects.filter(user=user)
    print('HamyonPayments to delete:', hp_qs.count())
    hp_qs.delete()

    tp_qs = TelegramPayment.objects.filter(order__user=user)
    print('TelegramPayments to delete:', tp_qs.count())
    tp_qs.delete()

    username = user.username
    user.delete()
    print('Deleted user', username)

if __name__ == '__main__':
    run()
