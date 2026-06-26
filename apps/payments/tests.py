from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from apps.payments.models import HamyonPayment
from apps.payments.services import HamyonPaymentService
from apps.telegram_services.models import TelegramOrder, TelegramPayment, TelegramProduct, TelegramProductCategory, TelegramProvider


class HamyonPaymentServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='hamyonuser', password='secret123')
        self.payment = HamyonPayment.objects.create(
            user=self.user,
            external_id='pay-123',
            amount=5067,
            requested_amount=5000,
            purpose=HamyonPayment.Purpose.WALLET_TOPUP,
            status=HamyonPayment.Status.PENDING,
            processed=False,
        )

    def test_process_payment_status_accepts_completed_provider_state(self):
        service = HamyonPaymentService(client=type('Client', (), {
            'get_payment_status': lambda self, payment_id, timeout=None: {'status': 'completed'}
        })())

        updated_payment = service.process_payment_status(self.payment)

        self.assertEqual(updated_payment.status, HamyonPayment.Status.SUCCESS)
        self.assertTrue(updated_payment.processed)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.balance, Decimal('5000'))

    def test_hamyon_payment_create_stores_fee_and_unique_amount_aliases(self):
        class FakeClient:
            def create_payment(self, amount):
                return {'payment_id': 'pay-456', 'card': '8600 1234 5678 9012'}

        service = HamyonPaymentService(client=FakeClient())
        payment = service.create_payment(
            self.user,
            amount=Decimal('10073'),
            requested_amount=Decimal('10000'),
            purpose=HamyonPayment.Purpose.WALLET_TOPUP,
            description='Auto topup test',
            metadata={'requested_amount': '10000'},
        )

        self.assertEqual(payment.fee_amount, Decimal('73'))
        self.assertEqual(payment.unique_amount, Decimal('10073'))
        self.assertEqual(payment.payment_id, 'pay-456')
        self.assertEqual(payment.requested_amount, Decimal('10000'))

    def test_check_hamyon_payment_status_confirms_order_on_success(self):
        category = TelegramProductCategory.objects.create(name='stars', display_name='Stars')
        provider = TelegramProvider.objects.create(name='custom', api_token='token', payment_method='stars')
        product = TelegramProduct.objects.create(
            category=category,
            provider=provider,
            seller=self.user,
            name='Test Stars',
            sku='test-stars',
            quantity=100,
            price_uzs=100000,
            status='active',
            auto_delivery=False,
        )
        order = TelegramOrder.objects.create(
            user=self.user,
            product=product,
            telegram_username='@testuser',
            status='waiting_payment',
            base_price=100000,
            unique_amount=100000,
            unique_code='TEST001',
        )
        TelegramPayment.objects.create(
            order=order,
            amount=100000,
            currency='UZS',
            payment_status='pending',
            payment_method='hamyon',
        )
        payment = HamyonPayment.objects.create(
            user=self.user,
            external_id='pay-success',
            amount=100000,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id),
            status=HamyonPayment.Status.PENDING,
            processed=False,
        )

        class FakeClient:
            def get_payment_status(self, payment_id, timeout=None):
                return {'status': 'paid'}

        self.client = FakeClient()
        service = HamyonPaymentService(client=self.client)
        with self.settings(HAMYON_SHOP_ID='shop', HAMYON_SHOP_KEY='key'):
            updated_payment = service.process_payment_status(payment)

        self.assertEqual(updated_payment.status, HamyonPayment.Status.SUCCESS)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
