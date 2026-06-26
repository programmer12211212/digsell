from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = 'GUEST', _('Guest')
        USER = 'USER', _('User')
        SELLER = 'SELLER', _('Seller')
        MODERATOR = 'MODERATOR', _('Moderator')
        ADMIN = 'ADMIN', _('Admin')
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')

    class LoyaltyLevel(models.TextChoices):
        BRONZE = 'BRONZE', _('Bronze')
        SILVER = 'SILVER', _('Silver')
        GOLD = 'GOLD', _('Gold')
        PLATINUM = 'PLATINUM', _('Platinum')
        DIAMOND = 'DIAMOND', _('Diamond')
        VIP = 'VIP', _('VIP')

    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_column='phone_number'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    loyalty_level = models.CharField(
        max_length=20, choices=LoyaltyLevel.choices, default=LoyaltyLevel.BRONZE
    )

    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )
    referral_code = models.CharField(max_length=50, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    telegram_id = models.CharField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    # Flag indicating whether the user has been approved as a seller
    is_seller_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import uuid
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bonus_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='UZS')
    cashback_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def bonus_points(self):
        return int(self.bonus_balance)

    @bonus_points.setter
    def bonus_points(self, value):
        self.bonus_balance = Decimal(str(value))

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance} UZS"

    def add_funds(self, amount, reason="TOPUP"):
        """Xavfsiz hamyonga pul qo'shish (Balans)."""
        from apps.payments.wallet_services import WalletService

        operation_type = WalletTransaction.OperationType.TOPUP
        if reason and 'bonus' in reason.lower():
            operation_type = WalletTransaction.OperationType.BONUS
        elif reason and 'admin' in reason.lower():
            operation_type = WalletTransaction.OperationType.ADMIN

        wallet = WalletService.credit(
            self.user,
            amount,
            operation_type=operation_type,
            description=reason,
        )
        self.balance = wallet.balance
        return wallet

    def add_bonus_funds(self, amount, reason="BONUS"):
        """Xavfsiz holda bonus ballarni qo'shish."""
        from django.db import transaction
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            wallet.bonus_balance += Decimal(str(amount))
            wallet.save(update_fields=['bonus_balance', 'updated_at'])
            
            self.bonus_balance = wallet.bonus_balance
            
            WalletTransaction.objects.create(
                wallet=wallet, 
                amount=amount, 
                tx_type='IN', 
                reason=reason
            )


class WalletTransaction(models.Model):
    class OperationType(models.TextChoices):
        TOPUP = 'TOPUP', 'Top-up'
        PURCHASE = 'PURCHASE', 'Purchase'
        REFUND = 'REFUND', 'Refund'
        ADMIN = 'ADMIN', 'Admin'
        TRANSFER = 'TRANSFER', 'Transfer'
        BONUS = 'BONUS', 'Bonus'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='tx_logs')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tx_type = models.CharField(max_length=3, choices=[('IN', 'Inflow'), ('OUT', 'Outflow')])
    reason = models.CharField(max_length=100)
    operation_type = models.CharField(
        max_length=20,
        choices=OperationType.choices,
        blank=True,
        default='',
    )
    balance_before = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    reference = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class SellerApplication(models.Model):
    """Application submitted by a user to become a seller."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        BANNED = 'BANNED', 'Banned'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_applications')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    resume = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    skills = models.CharField(max_length=512, help_text='Comma separated skills', blank=True)
    niche = models.CharField(max_length=100, help_text='e.g. Designer, Prompt maker, Programmer', blank=True)
    what_to_sell = models.CharField(max_length=255, blank=True, help_text='What products or services will you sell?')
    website = models.URLField(blank=True, null=True)
    portfolio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='seller_avatars/', null=True, blank=True)
    identity_document = models.ImageField(upload_to='seller_documents/', null=True, blank=True)
    agreed_to_terms = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Seller Application'
        verbose_name_plural = 'Seller Applications'

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"

    def _apply_approval(self):
        user = self.user
        if user.role not in (User.Role.ADMIN, User.Role.SUPER_ADMIN):
            user.role = User.Role.SELLER
        user.is_verified = True
        user.is_seller_approved = True
        if not user.is_active:
            user.is_active = True
        user.save(update_fields=['role', 'is_verified', 'is_seller_approved', 'is_active'])

    def _revoke_approval(self, banned=False):
        user = self.user
        if user.role == User.Role.SELLER:
            user.role = User.Role.USER
        user.is_seller_approved = False
        if banned:
            user.is_active = False
            user.save(update_fields=['role', 'is_seller_approved', 'is_active'])
        else:
            user.save(update_fields=['role', 'is_seller_approved'])

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = SellerApplication.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        super().save(*args, **kwargs)

        if previous_status != self.status:
            if self.status == self.Status.APPROVED:
                self._apply_approval()
            elif self.status == self.Status.BANNED:
                self._revoke_approval(banned=True)
            else:
                self._revoke_approval()
