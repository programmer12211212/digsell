from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from enum import Enum
import uuid
import random
import string

User = get_user_model()


class TelegramProvider(models.Model):
    """Telegram API Providers (e.g., Fragmently)"""
    
    PROVIDER_CHOICES = [
        ('fragmently', 'Fragmently'),
        ('custom', 'Custom API'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=PROVIDER_CHOICES)
    api_token = models.CharField(max_length=500, help_text="API Token/Key for the provider")
    wallet_version = models.CharField(max_length=50, default='v1', help_text="API Wallet Version")
    payment_method = models.CharField(max_length=100, default='stars', help_text="Payment method type")
    is_active = models.BooleanField(default=True)
    is_test = models.BooleanField(default=False, help_text="Test mode")
    
    # Balance tracking
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    stars_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    premium_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Telegram Provider'
        verbose_name_plural = 'Telegram Providers'
        indexes = [models.Index(fields=['is_active', 'name'])]
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"


class TelegramProductCategory(models.Model):
    """Categories for Telegram Services"""
    
    CATEGORY_CHOICES = [
        ('stars', 'Telegram Stars'),
        ('premium', 'Telegram Premium'),
        ('gifts', 'Telegram Gifts'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='⭐')
    color = models.CharField(max_length=7, default='#FFC300', help_text="Hex color code")
    image = models.ImageField(upload_to='telegram_services/categories/', blank=True, null=True, verbose_name="Category default image")
    
    class Meta:
        verbose_name = 'Telegram Product Category'
        verbose_name_plural = 'Telegram Product Categories'
    
    def __str__(self):
        return self.display_name


class TelegramProduct(models.Model):
    """Telegram Products (Stars, Premium, Gifts)"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(TelegramProductCategory, on_delete=models.PROTECT, related_name='products')
    provider = models.ForeignKey(TelegramProvider, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='telegram_products')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    
    # For Stars and Premium
    quantity = models.IntegerField(null=True, blank=True, help_text="Stars count or months for Premium")
    unit = models.CharField(max_length=50, default='stars', help_text="stars, months, gift_count")
    
    # Pricing
    price_uzs = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    price_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Image/Icon
    image = models.ImageField(upload_to='telegram_services/products/', blank=True)
    icon = models.CharField(max_length=50, default='⭐')
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    delivery_type = models.CharField(
        max_length=50, 
        default='instant',
        choices=[('instant', 'Instant'), ('scheduled', 'Scheduled')]
    )
    
    # Admin-managed settings
    auto_delivery = models.BooleanField(default=True)
    delivery_api_method = models.CharField(max_length=100, default='send_stars', help_text="API method name")
    
    stock = models.IntegerField(default=-1, help_text="-1 for unlimited")
    is_featured = models.BooleanField(default=False)
    
    # New fields for Enhanced Gifts
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common', null=True, blank=True)
    is_resale = models.BooleanField(default=False, help_text="Show Resale ribbon")
    price_stars = models.IntegerField(null=True, blank=True, help_text="Price in Telegram Stars")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Telegram Product'
        verbose_name_plural = 'Telegram Products'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['sku']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price_uzs} UZS"
    
    @property
    def is_available(self):
        return self.status == 'active' and (self.stock == -1 or self.stock > 0)


class TelegramPaymentCard(models.Model):
    """Payment Cards configured by Admin"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card_number = models.CharField(max_length=50)
    card_holder = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Telegram Payment Card'
        verbose_name_plural = 'Telegram Payment Cards'
    
    def __str__(self):
        return f"{self.bank_name} - {self.card_number[-4:]}"


class TelegramOrder(models.Model):
    """Telegram Service Orders"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('waiting_payment', 'Waiting Payment'),
        ('waiting_confirmation', 'Waiting Confirmation'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_orders')
    product = models.ForeignKey(TelegramProduct, on_delete=models.PROTECT)
    
    # User's Telegram info
    telegram_username = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^@?\w{5,32}$', 'Invalid Telegram username')]
    )
    telegram_user_id = models.CharField(max_length=20, blank=True)
    telegram_avatar = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='new')
    
    # Custom Quantity for Stars
    custom_quantity = models.IntegerField(null=True, blank=True, help_text="Override product quantity for custom orders")
    
    # Amount Information
    base_price = models.DecimalField(max_digits=15, decimal_places=2)
    unique_amount = models.DecimalField(max_digits=15, decimal_places=2)
    unique_code = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Payment Info
    payment_method = models.CharField(max_length=50, default='card_transfer')
    payment_card = models.ForeignKey(TelegramPaymentCard, on_delete=models.SET_NULL, null=True, blank=True)
    payment_screenshot = models.ImageField(upload_to='telegram_services/payments/', blank=True)
    
    # Delivery Info
    transaction_id = models.CharField(max_length=200, blank=True, unique=True, null=True)
    provider_response = models.JSONField(blank=True, null=True)
    delivery_attempts = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_confirmed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Telegram Order'
        verbose_name_plural = 'Telegram Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['telegram_username']),
            models.Index(fields=['unique_code']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.unique_code} - {self.telegram_username}"
    
    @property
    def formatted_unique_amount(self):
        return f"{self.unique_amount:,.0f}"


class TelegramPayment(models.Model):
    """Payment Transaction Records"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(TelegramOrder, on_delete=models.CASCADE, related_name='payment')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='UZS')
    
    payment_status = models.CharField(
        max_length=25,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    
    payment_method = models.CharField(max_length=50, default='card_transfer')
    payment_details = models.JSONField(blank=True, null=True)
    
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_payments')
    confirmation_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Telegram Payment'
        verbose_name_plural = 'Telegram Payments'
        indexes = [models.Index(fields=['payment_status', 'created_at'])]
    
    def __str__(self):
        try:
            return f"Payment {self.order.unique_code} - {self.amount}"
        except Exception:
            return f"Payment {self.id} - {self.amount}"


class TelegramGift(models.Model):
    """Custom Telegram Gifts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='telegram_services/gifts/')
    price_uzs = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    provider = models.ForeignKey(TelegramProvider, on_delete=models.SET_NULL, null=True, blank=True)
    provider_gift_id = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Telegram Gift'
        verbose_name_plural = 'Telegram Gifts'
    
    def __str__(self):
        return self.name


class TelegramProviderLog(models.Model):
    """Logs for provider API calls"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(TelegramProvider, on_delete=models.CASCADE, related_name='logs')
    order = models.ForeignKey(TelegramOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    method = models.CharField(max_length=100)
    endpoint = models.URLField()
    request_data = models.JSONField()
    response_data = models.JSONField(blank=True, null=True)
    
    status_code = models.IntegerField(null=True, blank=True)
    error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Telegram Provider Log'
        verbose_name_plural = 'Telegram Provider Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'created_at']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.method} - {self.status_code}"


class TelegramOrderLog(models.Model):
    """Logs for order status changes and events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(TelegramOrder, on_delete=models.CASCADE, related_name='logs')
    
    action = models.CharField(max_length=100)
    status_from = models.CharField(max_length=25, blank=True)
    status_to = models.CharField(max_length=25, blank=True)
    
    message = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Telegram Order Log'
        verbose_name_plural = 'Telegram Order Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.order.unique_code} - {self.action}"


class TelegramNotification(models.Model):
    """Notifications for users"""
    
    NOTIFICATION_TYPES = [
        ('order_created', 'Order Created'),
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('delivery_processing', 'Delivery Processing'),
        ('delivery_completed', 'Delivery Completed'),
        ('delivery_failed', 'Delivery Failed'),
        ('refund_issued', 'Refund Issued'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_notifications')
    order = models.ForeignKey(TelegramOrder, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Telegram Notification'
        verbose_name_plural = 'Telegram Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class TelegramSettings(models.Model):
    """Global settings for Telegram Services"""
    
    # Enable/Disable Service
    service_enabled = models.BooleanField(default=True)
    
    # Payment Settings
    min_order_amount = models.DecimalField(max_digits=15, decimal_places=2, default=1000)
    max_order_amount = models.DecimalField(max_digits=15, decimal_places=2, default=50000000)
    payment_confirmation_timeout = models.IntegerField(default=3600, help_text="Seconds")
    
    # Delivery Settings
    auto_delivery_enabled = models.BooleanField(default=True)
    max_delivery_retries = models.IntegerField(default=3)
    delivery_retry_interval = models.IntegerField(default=300, help_text="Seconds")
    
    # Fees
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    
    # Contact Info
    support_email = models.EmailField(default='support@Digsell.uz')
    support_telegram = models.CharField(max_length=100, default='@digsell_support')
    
    # Gift Sales Settings
    gifts_telegram_username = models.CharField(
        max_length=100, 
        default='@slx15', 
        help_text="Destination Telegram username for Gifts purchase redirect"
    )
    gifts_message_template = models.TextField(
        default="""━━━━━━━━━━━━━━
🎁 GIFT PURCHASE REQUEST
━━━━━━━━━━━━━━

👤 User: @{username}

🎁 Gift:
{gift_name}

💰 Price:
{price} UZS

🆔 Product ID:
#{product_id}

📅 Date:
{current_date}

🌐 Source:
Digsell.uz

━━━━━━━━━━━━━━

Assalomu alaykum.

Men ushbu giftni sotib olmoqchiman.
Iltimos, xarid jarayonini boshlashga yordam bering.

Rahmat.""",
        help_text="Template for pre-filled Telegram message"
    )
    gifts_redirect_enabled = models.BooleanField(
        default=True, 
        help_text="Enable/Disable redirecting to Telegram for Gifts"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings
    
    class Meta:
        verbose_name = 'Telegram Settings'
        verbose_name_plural = 'Telegram Settings'
    
    def __str__(self):
        return "Telegram Services Settings"
