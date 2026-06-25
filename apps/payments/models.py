import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.utils import format_uzs
from apps.marketplace.models import Category

class EscrowAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="escrow_wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    frozen_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Hamyon"
        verbose_name_plural = "Hamyonlar"

    def __str__(self):
        return f"{self.user.username} Escrow - Frozen: {format_uzs(self.frozen_balance)}"

    @property
    def total_balance(self):
        from apps.users.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        return wallet.balance

    @total_balance.setter
    def total_balance(self, value):
        from apps.users.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.balance = value
        wallet.save()


class UserCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    card_number = models.CharField(max_length=20)
    card_holder = models.CharField(max_length=100)
    expiry_date = models.CharField(max_length=5)  # MM/YY
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi kartasi"
        verbose_name_plural = "Foydalanuvchi kartalari"

    def __str__(self):
        return f"**** {self.card_number[-4:]} - {self.user.username}"


class CompanyCard(models.Model):
    card_number = models.CharField(max_length=20, verbose_name="Karta raqami")
    card_name = models.CharField(max_length=50, verbose_name="Karta turi", help_text="Masalan: Uzcard, Humo, Visa")
    card_holder = models.CharField(max_length=100, verbose_name="Karta egasi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kompaniya kartasi"
        verbose_name_plural = "Kompaniya kartalari"

    def __str__(self):
        return f"{self.card_name} - {self.card_number} ({self.card_holder})"


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"
        ordering = ['-created_at']


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        FIXED = "FIXED", "Fixed amount"
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FREE_SERVICE = "FREE_SERVICE", "Free service fee"
        SUBSCRIPTION = "SUBSCRIPTION", "Subscription discount"
        FIRST_ORDER = "FIRST_ORDER", "First order"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.FIXED)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_premium_only = models.BooleanField(default=False)
    is_new_user_only = models.BooleanField(default=False)
    allowed_categories = models.ManyToManyField(Category, blank=True, related_name='coupons')
    allowed_sellers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='seller_coupons')
    apply_to_marketplace = models.BooleanField(default=True)
    apply_to_subscription = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kuponlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def clean(self):
        self.code = (self.code or '').strip().upper()
        if self.valid_until <= self.valid_from:
            raise ValidationError("Coupon valid_until must be after valid_from.")
        if self.discount_type == self.DiscountType.FREE_SERVICE:
            self.discount_value = Decimal('0')

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        super().save(*args, **kwargs)

    def is_expired(self):
        now = timezone.now()
        return self.valid_until < now or self.valid_from > now

    def is_available(self):
        if not self.is_active or self.is_expired():
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, order):
        price = order.amount
        discount = Decimal('0')
        commission = order.commission
        if self.discount_type == self.DiscountType.FIXED:
            discount = min(self.discount_value, price)
        elif self.discount_type == self.DiscountType.PERCENTAGE:
            discount = (price * self.discount_value / Decimal('100')).quantize(Decimal('0.01'))
        elif self.discount_type == self.DiscountType.FREE_SERVICE:
            discount = Decimal('0')
            commission = Decimal('0')
        elif self.discount_type == self.DiscountType.SUBSCRIPTION:
            discount = min(self.discount_value, price)
        elif self.discount_type == self.DiscountType.FIRST_ORDER:
            discount = min(self.discount_value, price)

        if self.max_discount is not None and discount > self.max_discount:
            discount = self.max_discount

        final_amount = max(price - discount, Decimal('0.00'))
        return {
            'discount_amount': discount,
            'final_amount': final_amount,
            'commission': commission,
        }

    def register_usage(self, user, order, amount_saved, ip_address=None):
        CouponUsage.objects.create(
            coupon=self,
            user=user,
            order=order,
            amount_saved=amount_saved,
            ip_address=ip_address or '',
        )
        self.used_count = models.F('used_count') + 1
        self.save(update_fields=['used_count'])

    def user_usage_count(self, user):
        return CouponUsage.objects.filter(coupon=self, user=user).count()

    def is_valid_for_order(self, order, user):
        now = timezone.now()
        if not self.is_active:
            raise ValidationError("Promo kod faollashtirilmagan.")
        if self.valid_from > now or self.valid_until < now:
            raise ValidationError("Promo kod muddati o'tgan yoki hali amal qilmaydi.")
        if self.usage_limit and self.used_count >= self.usage_limit:
            raise ValidationError("Bu promo koddan foydalanish limiti tugagan.")
        if self.per_user_limit and self.user_usage_count(user) >= self.per_user_limit:
            raise ValidationError("Siz ushbu promo koddan ko'p marta foydalangan ekansiz.")
        if self.minimum_amount and order.amount < self.minimum_amount:
            raise ValidationError(f"Buyurtma summasi kamida {format_uzs(self.minimum_amount)} bo'lishi kerak.")
        if self.is_new_user_only and order.buyer.orders.filter(status__in=['PAID', 'COMPLETED']).exists():
            raise ValidationError("Bu promo kod faqat yangi foydalanuvchilar uchun.")
        if self.is_premium_only and (not hasattr(user, 'user_subscription') or not user.user_subscription.is_active or user.user_subscription.plan == 'FREE'):
            raise ValidationError("Bu promo kod faqat premium foydalanuvchilar uchun.")
        if order.product and not self.apply_to_marketplace:
            raise ValidationError("Bu promo kod marketplace xaridlari uchun amal qilmaydi.")
        if not order.product and not self.apply_to_subscription:
            raise ValidationError("Bu promo kod obuna xaridi uchun amal qilmaydi.")
        if self.allowed_categories.exists() and order.product and order.product.category not in self.allowed_categories.all():
            raise ValidationError("Bu promo kod tanlangan kategoriya uchun amal qilmaydi.")
        if self.allowed_sellers.exists() and order.product and order.product.seller not in self.allowed_sellers.all():
            raise ValidationError("Bu promo kod tanlangan sotuvchilar uchun amal qilmaydi.")
        if self.discount_type == self.DiscountType.FIRST_ORDER and order.buyer.orders.filter(status__in=['PAID', 'COMPLETED']).exclude(id=order.id).exists():
            raise ValidationError("Bu promo kod faqat birinchi buyurtma uchun amal qiladi.")
        return True


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    amount_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ip_address = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kupon ishlatilishi"
        verbose_name_plural = "Kupon ishlatilishi"

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.username}"


class CouponValidationAttempt(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='validation_attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=30)
    ip_address = models.CharField(max_length=50, blank=True)
    is_success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kupon tekshiruvi"
        verbose_name_plural = "Kupon tekshiruvlari"

    def __str__(self):
        return f"Coupon attempt {self.code} for {self.user or 'anonymous'} - {'success' if self.is_success else 'failed'}"


class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Kutilmoqda"
        APPROVED = "APPROVED", "Tasdiqlandi"
        REJECTED = "REJECTED", "Rad etildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    card = models.ForeignKey(UserCard, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pul yechish so'rovi"
        verbose_name_plural = "Pul yechish so'rovlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {format_uzs(self.amount)} ({self.status})"

    def save(self, *args, **kwargs):
        is_approved = self.status == self.Status.APPROVED
        
        if self.pk:
            old_self = WithdrawalRequest.objects.get(pk=self.pk)
            if old_self.status != self.Status.APPROVED and is_approved:
                from apps.users.models import Wallet, WalletTransaction
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                
                # Check if balance is enough (safety check)
                if wallet.balance >= self.amount:
                    from django.db import transaction
                    with transaction.atomic():
                        w = Wallet.objects.select_for_update().get(pk=wallet.pk)
                        w.balance -= self.amount
                        w.save(update_fields=['balance', 'updated_at'])
                        WalletTransaction.objects.create(
                            wallet=w, amount=self.amount, tx_type='OUT', 
                            reason=f"Yechib olish tasdiqlandi: #{self.id}"
                        )
                else:
                    # If balance is not enough, we might want to prevent approval or log error
                    # For now just log and continue, although this shouldn't happen if validation is correct
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Insufficient funds for withdrawal #{self.id} for user {self.user.username}")

        super().save(*args, **kwargs)


class DepositRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Kutilmoqda"
        APPROVED = "APPROVED", "Tasdiqlandi"
        REJECTED = "REJECTED", "Rad etildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposits")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    receipt_image = models.ImageField(upload_to="deposit_receipts/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balans to'ldirish so'rovi"
        verbose_name_plural = "Balans to'ldirish so'rovlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.amount} UZS ({self.status})"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        is_approved = self.status == self.Status.APPROVED
        
        if is_new and is_approved:
            from apps.users.models import Wallet
            wallet, _ = Wallet.objects.get_or_create(user=self.user)
            wallet.add_funds(self.amount, reason="Deposit (Created as Approved)")
        elif self.pk:
            old_self = DepositRequest.objects.get(pk=self.pk)
            if old_self.status != self.Status.APPROVED and is_approved:
                from apps.users.models import Wallet
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                wallet.add_funds(self.amount, reason="Deposit Approved")
                
        super().save(*args, **kwargs)

