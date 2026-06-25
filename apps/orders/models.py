from django.db import models
from django.conf import settings
from apps.videos.models import Video
import uuid

class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'Yangi'
        PENDING = 'PENDING', 'To\'lov kutilmoqda'
        PAID = 'PAID', 'To\'langan'
        PROCESSING = 'PROCESSING', 'Ishlov berilmoqda'
        SHIPPED = 'SHIPPED', 'Yuborildi'
        DELIVERED = 'DELIVERED', 'Yetkazildi'
        COMPLETED = 'COMPLETED', 'Yakunlandi'
        CANCELLED = 'CANCELLED', 'Bekor qilindi'
        REFUNDED = 'REFUNDED', 'Qaytarildi'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Tracking for Physical Products
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    coupon_code = models.CharField(max_length=50, blank=True, default='')
    receipt_image = models.ImageField(upload_to='receipts/%Y/%m/', blank=True, null=True)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Order {self.id} | {self.status}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_status = None
        if not is_new:
            try:
                old_status = Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            except Exception:
                pass
                
        super().save(*args, **kwargs)
        
        if getattr(self, '_completing', False):
            return
            
        if self.status in (self.Status.PAID, self.Status.COMPLETED) and old_status not in (self.Status.PAID, self.Status.COMPLETED):
            self._completing = True
            try:
                from apps.marketplace.views import _complete_order
                _complete_order(self, self.buyer)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-complete order {self.id} on save: {str(e)}")
            finally:
                self._completing = False

    @property
    def product(self):
        item = self.items.select_related('product').first()
        return item.product if item else None

    @property
    def amount(self):
        return self.total_amount

    @property
    def commission(self):
        if self.commission_amount:
            return self.commission_amount
        from decimal import Decimal
        return (self.total_amount * Decimal('0.10')).quantize(Decimal('0.01'))

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Video, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total(self):
        from decimal import Decimal
        total = Decimal('0')
        for item in self.items.select_related('product'):
            price = item.product.discount_price or item.product.price
            total += price * item.quantity
        return total

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Video, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    saved_for_later = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

    @property
    def subtotal(self):
        price = self.product.discount_price or self.product.price
        return price * self.quantity


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
