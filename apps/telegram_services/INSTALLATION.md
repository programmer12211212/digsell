# Telegram Services Module - Installation & Setup Guide

## Overview

The Telegram Services module is a premium, production-ready Django app that enables users to purchase Telegram Stars, Premium subscriptions, and Exclusive Gifts directly from the Digsell.uz platform.

## Features

### Core Features
✅ **Telegram Stars Purchase** - 50, 100, 250, 500, 1000, 5000+ stars  
✅ **Premium Subscriptions** - 3, 6, 12 months  
✅ **Exclusive Gifts** - Admin-managed custom gifts  
✅ **Instant Delivery** - Automatic processing via Fragmently API  
✅ **Unique Payment Amounts** - Each order gets a unique amount for identification  
✅ **Manual Card Transfer** - Admin-configured payment cards  
✅ **Full Admin Panel** - Complete management interface  

### Design Features
✅ **Premium UI** - Glassmorphism, gradients, animations  
✅ **Dark/Light Mode** - Automatic system preference detection  
✅ **Mobile First** - Fully responsive design  
✅ **Animated Transitions** - Smooth, professional animations  
✅ **Skeleton Loading** - Modern loading states  
✅ **Toast Notifications** - Beautiful notification system  

---

## Installation Steps

### 1. **App Already Created**

The app structure is already in place:
```
apps/telegram_services/
├── migrations/          # Database migrations
├── static/             # CSS, JavaScript
├── templates/          # HTML templates
├── admin.py            # Admin interface
├── apps.py             # App configuration
├── forms.py            # Form classes
├── models.py           # Database models
├── serializers.py      # DRF serializers
├── services.py         # Business logic
├── signals.py          # Django signals
├── urls.py             # URL routing
├── views.py            # View logic
└── __init__.py
```

### 2. **Run Migrations**

```bash
python manage.py makemigrations
python manage.py migrate apps.telegram_services
```

### 3. **Create Superuser (if not exists)**

```bash
python manage.py createsuperuser
```

### 4. **Add Initial Data (Optional)**

Create a management command file at `apps/telegram_services/management/commands/init_telegram_services.py`:

```python
from django.core.management.base import BaseCommand
from apps.telegram_services.models import (
    TelegramProductCategory, TelegramSettings
)

class Command(BaseCommand):
    help = 'Initialize Telegram Services with default data'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {
                'name': 'stars',
                'display_name': 'Telegram Stars',
                'description': 'Purchase Telegram Stars for gifts and boosts',
                'icon': '⭐',
                'color': '#FFC300'
            },
            {
                'name': 'premium',
                'display_name': 'Telegram Premium',
                'description': 'Get Premium features and exclusive perks',
                'icon': '💎',
                'color': '#17A2B8'
            },
            {
                'name': 'gifts',
                'display_name': 'Telegram Gifts',
                'description': 'Send exclusive gifts to your friends',
                'icon': '🎁',
                'color': '#DC3545'
            }
        ]
        
        for cat_data in categories_data:
            TelegramProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'display_name': cat_data['display_name'],
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                }
            )
        
        # Create default settings
        TelegramSettings.objects.get_or_create(
            instance=None,
            defaults={
                'service_enabled': True,
                'min_order_amount': 1000,
                'max_order_amount': 50000000,
                'payment_confirmation_timeout': 3600,
                'auto_delivery_enabled': True,
                'max_delivery_retries': 3,
                'delivery_retry_interval': 300,
                'commission_percentage': 5,
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Telegram Services initialized successfully'))
```

Run it:
```bash
python manage.py init_telegram_services
```

### 5. **Configure Fragmently Provider (Optional)**

To enable auto-delivery, you need a Fragmently API account:

```python
# Via Django shell
python manage.py shell

from apps.telegram_services.models import TelegramProvider

TelegramProvider.objects.create(
    name='fragmently',
    api_token='your_fragmently_api_token_here',
    wallet_version='v1',
    is_active=True,
    is_test=False
)
```

Or create via Admin Panel at `/admin/telegram_services/telegramprovider/`

### 6. **Add Payment Cards (Required)**

Add payment card details via Admin Panel at `/admin/telegram_services/telegrampaymentcard/`

Example:
- Card Number: `9860 1000 1111 1111`
- Card Holder: `John Doe`
- Bank Name: `Universal Bank`

### 7. **Create Products**

Via Admin Panel at `/admin/telegram_services/telegramproduct/`

Example Stars Products:
```
- 50 Stars - 1,000 UZS
- 100 Stars - 1,900 UZS
- 250 Stars - 4,500 UZS
- 500 Stars - 8,900 UZS
- 1000 Stars - 17,500 UZS
```

### 8. **Access the Platform**

- User Interface: `http://localhost:8000/telegram-services/`
- Admin Panel: `http://localhost:8000/admin/telegram_services/`

---

## Configuration

### Settings (in Admin Panel)

Navigate to `/admin/telegram_services/telegramsettings/`:

- **Min Order Amount**: 1000 UZS
- **Max Order Amount**: 50,000,000 UZS
- **Payment Confirmation Timeout**: 3600 seconds
- **Auto Delivery**: Enabled
- **Commission**: 5%
- **Support Email**: support@Digsell.uz
- **Support Telegram**: @digsell_support

---

## Usage

### For Users

1. Visit `/telegram-services/`
2. Browse products by category
3. Click "Buy Now" on a product
4. Enter Telegram username
5. Transfer payment to bank card
6. Click "I've Transferred the Money"
7. Wait for admin verification
8. Auto-delivery starts automatically

### For Admins

#### Managing Products
1. Go to `/admin/telegram_services/telegramproduct/`
2. Add/Edit/Delete products
3. Set prices, quantities, status
4. Configure auto-delivery settings

#### Managing Orders
1. Go to `/admin/telegram_services/telegramorder/`
2. View pending orders
3. Click "Confirm Payment" to verify payment
4. System auto-delivers or mark as completed
5. Use bulk actions for mass operations

#### Managing Payments
1. Go to `/admin/telegram_services/telegrampayment/`
2. Verify payment details
3. Confirm payments manually
4. View payment history

#### Monitoring
1. Check provider logs: `/admin/telegram_services/telegramproviderlog/`
2. View order logs: `/admin/telegram_services/telegramorderlog/`
3. Track provider balance: `/admin/telegram_services/telegramprovider/`

---

## API Endpoints

### Public Endpoints

```
GET /telegram-services/api/products/
  - List all active products
  - Query params: category, search

POST /telegram-services/api/user-info/?username=@username
  - Get Telegram user info
```

### Authenticated Endpoints

```
GET /telegram-services/api/my-orders/
  - Get user's orders
  - Requires authentication

POST /telegram-services/orders/create/<product_id>/
  - Create new order
  - Requires authentication
  - Body: { "telegram_username": "@username" }

POST /telegram-services/orders/<order_id>/confirm-payment/
  - Confirm payment for order
  - Requires authentication
```

---

## Database Schema

### Models

#### TelegramProvider
- API integration for Fragmently
- Stores API tokens and balances
- Tracks provider status

#### TelegramProductCategory
- Stars, Premium, Gifts categories
- Display names and icons
- Color schemes

#### TelegramProduct
- Individual products (50 stars, 3-month premium, etc.)
- Pricing and inventory
- Delivery configuration

#### TelegramOrder
- User orders with unique amount
- Telegram user information
- Payment and delivery tracking

#### TelegramPayment
- Payment transaction records
- Payment status tracking
- Confirmation details

#### TelegramOrderLog
- Order status history
- All actions and changes
- Audit trail

#### TelegramProviderLog
- API call logs
- Request/response data
- Error tracking

#### TelegramNotification
- User notifications
- Order status updates
- Delivery confirmations

#### TelegramSettings
- Global configuration
- Payment settings
- Support information

---

## Security Features

✅ **CSRF Protection** - Django built-in CSRF tokens  
✅ **XSS Prevention** - Template auto-escaping  
✅ **SQL Injection Protection** - ORM queries  
✅ **Rate Limiting** - Django Axes integration  
✅ **Secure APIs** - JWT authentication ready  
✅ **Audit Logs** - Full action tracking  
✅ **Permission Checks** - Admin-only operations  

---

## Troubleshooting

### Migration Issues

```bash
# Reset migrations (development only)
python manage.py migrate apps.telegram_services zero
python manage.py migrate apps.telegram_services

# Check migration status
python manage.py showmigrations apps.telegram_services
```

### Provider Connection Issues

1. Check API token in admin
2. Verify firewall/proxy settings
3. Test connection: `/admin/telegram_services/telegramprovider/` → "Test API"
4. Check logs: `/admin/telegram_services/telegramproviderlog/`

### Payment Not Confirming

1. Verify unique amount matches transfer
2. Check order status in admin
3. Review order logs for errors
4. Check provider logs for delivery errors

---

## Performance Optimization

### Caching
- Product cache invalidation on save
- Category cache for lists
- User order cache

### Database
- Indexed fields for fast queries
- Efficient pagination
- Aggregation queries for stats

### Frontend
- Lazy loading for images
- CSS/JS minification
- Browser caching headers

---

## Backup & Maintenance

### Regular Tasks

```bash
# Export data
python manage.py dumpdata apps.telegram_services > telegram_services_backup.json

# Import data
python manage.py loaddata telegram_services_backup.json

# Check order status
python manage.py shell
>>> from apps.telegram_services.models import TelegramOrder
>>> TelegramOrder.objects.filter(status='processing').count()
```

---

## Support & Resources

- **Email**: support@Digsell.uz
- **Telegram**: @digsell_support
- **Documentation**: This file
- **Admin Panel**: `/admin/telegram_services/`

---

## License

This module is part of Digsell.uz and follows the same license terms.

---

## Version Info

- **Version**: 1.0.0
- **Created**: 2026-06-23
- **Framework**: Django 5.1+
- **Python**: 3.9+

---

## Next Steps After Installation

1. ✅ Run migrations
2. ✅ Create admin user
3. ✅ Add payment cards
4. ✅ Configure provider
5. ✅ Create products
6. ✅ Test order flow
7. ✅ Monitor logs
8. ✅ Go live!

---

**Need help?** Contact support@Digsell.uz or visit `/admin/` for management interface.
