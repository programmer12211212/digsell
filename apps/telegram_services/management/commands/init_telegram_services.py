from django.core.management.base import BaseCommand
from apps.telegram_services.models import (
    TelegramProductCategory, TelegramProduct, TelegramPaymentCard,
    TelegramProvider, TelegramGift, TelegramSettings
)
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize Telegram Services with premium product data and settings'

    def handle(self, *args, **options):
        # 1. Create categories
        self.stdout.write('Creating categories...')
        categories_data = [
            {
                'name': 'stars',
                'display_name': 'Telegram Stars',
                'description': 'Buy Telegram Stars for gifts, channels, and apps instantly',
                'icon': '⭐',
                'color': '#FFC300'
            },
            {
                'name': 'premium',
                'display_name': 'Telegram Premium',
                'description': 'Unlock Telegram Premium benefits and exclusive icons',
                'icon': '💎',
                'color': '#17A2B8'
            },
            {
                'name': 'gifts',
                'display_name': 'Telegram Gifts',
                'description': 'Send limited-edition custom gifts to your friends and loved ones',
                'icon': '🎁',
                'color': '#DC3545'
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = TelegramProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'display_name': cat_data['display_name'],
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                }
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {cat.display_name}"))
            else:
                self.stdout.write(f"Category already exists: {cat.display_name}")

        # 2. Create Default Provider
        self.stdout.write('\nCreating default Telegram provider...')
        provider, created = TelegramProvider.objects.get_or_create(
            name='fragmently',
            defaults={
                'api_token': 'dd7e81424518d0403ad4179356f6f7def795565e0786c16395d9747d977e4306',
                'wallet_version': 'V4R2',
                'payment_method': 'ton',
                'is_active': True,
                'is_test': False,
                'balance': Decimal('1500000.00'),
                'stars_balance': Decimal('50000.00'),
                'premium_balance': Decimal('120.00'),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created provider: {provider.name}"))
        else:
            self.stdout.write(f"Provider already exists: {provider.name}")

        # 3. Create Default Payment Card
        self.stdout.write('\nCreating default payment card...')
        card, created = TelegramPaymentCard.objects.get_or_create(
            card_number='9860 1000 1111 1111',
            defaults={
                'card_holder': 'Digsell.uz Admin',
                'bank_name': 'Universal Bank',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created payment card: {card.bank_name} - {card.card_number}"))
        else:
            self.stdout.write(f"Payment card already exists: {card.bank_name}")

        # 4. Create default products
        self.stdout.write('\nCreating products...')
        
        # Stars Products
        stars_products = [
            {'sku': 'stars_50', 'name': '50 Telegram Stars', 'quantity': 50, 'price': 1500, 'featured': True},
            {'sku': 'stars_100', 'name': '100 Telegram Stars', 'quantity': 100, 'price': 22000, 'featured': True},
            {'sku': 'stars_250', 'name': '250 Telegram Stars', 'quantity': 250, 'price': 52000, 'featured': False},
            {'sku': 'stars_500', 'name': '500 Telegram Stars', 'quantity': 500, 'price': 100000, 'featured': True},
            {'sku': 'stars_1000', 'name': '1000 Telegram Stars', 'quantity': 1000, 'price': 190000, 'featured': False},
            {'sku': 'stars_5000', 'name': '5000 Telegram Stars', 'quantity': 5000, 'price': 900000, 'featured': False},
        ]
        for prod in stars_products:
            p, created = TelegramProduct.objects.get_or_create(
                sku=prod['sku'],
                defaults={
                    'category': categories['stars'],
                    'provider': provider,
                    'name': prod['name'],
                    'description': f"Purchase {prod['quantity']} Telegram Stars directly to your account.",
                    'quantity': prod['quantity'],
                    'unit': 'stars',
                    'price_uzs': Decimal(str(prod['price'])),
                    'price_usd': Decimal(str(prod['price'] / 12600)), # Approximate USD conversion
                    'icon': '⭐',
                    'status': 'active',
                    'auto_delivery': True,
                    'delivery_api_method': 'send_stars',
                    'is_featured': prod['featured']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {p.name}"))

        # Premium Products
        premium_products = [
            {'sku': 'premium_3m', 'name': '3 Months Telegram Premium', 'quantity': 3, 'price': 120000, 'featured': True},
            {'sku': 'premium_6m', 'name': '6 Months Telegram Premium', 'quantity': 6, 'price': 220000, 'featured': True},
            {'sku': 'premium_12m', 'name': '12 Months Telegram Premium', 'quantity': 12, 'price': 400000, 'featured': True},
        ]
        for prod in premium_products:
            p, created = TelegramProduct.objects.get_or_create(
                sku=prod['sku'],
                defaults={
                    'category': categories['premium'],
                    'provider': provider,
                    'name': prod['name'],
                    'description': f"Subscribe to Telegram Premium for {prod['quantity']} months to get animated emojis, larger uploads, and more.",
                    'quantity': prod['quantity'],
                    'unit': 'months',
                    'price_uzs': Decimal(str(prod['price'])),
                    'price_usd': Decimal(str(prod['price'] / 12600)),
                    'icon': '💎',
                    'status': 'active',
                    'auto_delivery': True,
                    'delivery_api_method': 'send_premium',
                    'is_featured': prod['featured']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {p.name}"))

        # Gifts Products
        gifts_products = [
            {'sku': 'gift_stars', 'name': 'Exclusive Telegram Star Gift', 'price': 15000, 'desc': 'A classic glowing Telegram star gift for your profile.', 'icon': '🎁', 'featured': True},
            {'sku': 'gift_box', 'name': 'Premium Mystery Box', 'price': 65000, 'desc': 'Open a mystery box filled with premium Telegram features and stars.', 'icon': '📦', 'featured': True},
            {'sku': 'gift_crown', 'name': 'Diamond Crown Gift', 'price': 120000, 'desc': 'Showcase royalty with this diamond-crusted premium crown gift.', 'icon': '👑', 'featured': True},
        ]
        for prod in gifts_products:
            p, created = TelegramProduct.objects.get_or_create(
                sku=prod['sku'],
                defaults={
                    'category': categories['gifts'],
                    'provider': provider,
                    'name': prod['name'],
                    'description': prod['desc'],
                    'quantity': 1,
                    'unit': 'gift_count',
                    'price_uzs': Decimal(str(prod['price'])),
                    'price_usd': Decimal(str(prod['price'] / 12600)),
                    'icon': prod['icon'],
                    'status': 'active',
                    'auto_delivery': True,
                    'delivery_api_method': 'send_gift',
                    'is_featured': prod['featured']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {p.name}"))

        # 5. Create Telegram Gifts
        self.stdout.write('\nCreating Telegram Gifts records...')
        for prod in gifts_products:
            g, created = TelegramGift.objects.get_or_create(
                provider_gift_id=prod['sku'],
                defaults={
                    'name': prod['name'],
                    'description': prod['desc'],
                    'price_uzs': Decimal(str(prod['price'])),
                    'provider': provider,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created gift: {g.name}"))

        # 6. Create default settings
        self.stdout.write('\nCreating default settings...')
        settings, created = TelegramSettings.objects.get_or_create(
            defaults={
                'service_enabled': True,
                'min_order_amount': Decimal('1000.00'),
                'max_order_amount': Decimal('50000000.00'),
                'payment_confirmation_timeout': 3600,
                'auto_delivery_enabled': True,
                'max_delivery_retries': 3,
                'delivery_retry_interval': 300,
                'commission_percentage': Decimal('5.00'),
                'support_email': 'support@Digsell.uz',
                'support_telegram': '@digsell_support',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created global settings"))
        else:
            self.stdout.write("Global settings already exist")

        self.stdout.write(self.style.SUCCESS('\nTelegram Services initialized successfully!'))
