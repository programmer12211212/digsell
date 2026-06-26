from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.payments.models import HamyonPayment
from apps.telegram_services.models import TelegramOrder, TelegramProduct, TelegramProductCategory
from apps.telegram_services.views import build_gift_admin_contact_payload


class GiftAdminContactFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='giftadminuser',
            email='giftadmin@example.com',
            first_name='Ali',
            last_name='Valiyev',
        )
        self.category = TelegramProductCategory.objects.create(
            name='gifts',
            display_name='Telegram Gifts',
            icon='🎁',
        )
        self.product = TelegramProduct.objects.create(
            category=self.category,
            sku='gift_test_box',
            name='Gift Test Box',
            price_uzs=Decimal('50000'),
            status='active',
            stock=10,
            unit='gift_count',
            delivery_api_method='send_gift',
        )
        self.order = TelegramOrder.objects.create(
            user=self.user,
            product=self.product,
            telegram_username='@giftuser',
            telegram_user_id='123456789',
            base_price=Decimal('50000'),
            unique_amount=Decimal('50000'),
            unique_code='GIFT001',
            status='paid',
        )
        self.payment = HamyonPayment.objects.create(
            user=self.user,
            external_id='HAMYON-001',
            amount=Decimal('50000'),
            requested_amount=Decimal('50000'),
            fee_amount=Decimal('0'),
            status=HamyonPayment.Status.SUCCESS,
            paid_at=timezone.now(),
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(self.order.id),
        )

    def test_gift_admin_contact_payload_includes_required_details(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        payload = build_gift_admin_contact_payload(request, self.order, self.payment)

        self.assertTrue(payload['is_visible'])
        self.assertIn('https://t.me/uzwwn', payload['url'])
        self.assertIn('Salom.', payload['message'])
        self.assertIn('Buyurtma ID:', payload['message'])
        self.assertIn('Unique ID:', payload['message'])
        self.assertIn('Gift Name:', payload['message'])
        self.assertIn('Gift Category:', payload['message'])
        self.assertIn('Gift Quantity:', payload['message'])
        self.assertIn('Gift Price:', payload['message'])
        self.assertIn('Requested Amount:', payload['message'])
        self.assertIn('Paid Amount:', payload['message'])
        self.assertIn('Payment ID:', payload['message'])
        self.assertIn('Transaction ID:', payload['message'])
        self.assertIn('Payment Method:', payload['message'])
        self.assertIn('Payment Date & Time:', payload['message'])
        self.assertIn('Customer Username:', payload['message'])
        self.assertIn('Customer Full Name:', payload['message'])
        self.assertIn('Telegram Username:', payload['message'])
        self.assertIn('Telegram User ID:', payload['message'])
        self.assertIn('Order Status:', payload['message'])
        self.assertIn('Delivery Status:', payload['message'])
