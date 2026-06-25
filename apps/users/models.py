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
        from django.db import transaction
        with transaction.atomic():
            # Refresh and lock the wallet row
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            wallet.balance += Decimal(str(amount))
            wallet.save(update_fields=['balance', 'updated_at'])
            
            # Update the current instance to match
            self.balance = wallet.balance
            
            WalletTransaction.objects.create(
                wallet=wallet, 
                amount=amount, 
                tx_type='IN', 
                reason=reason
            )

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
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='tx_logs')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tx_type = models.CharField(max_length=3, choices=[('IN', 'Inflow'), ('OUT', 'Outflow')])
    reason = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class SellerApplication(models.Model):
    """Application submitted by a user to become a seller."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_applications')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    resume = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='seller_avatars/', null=True, blank=True)
    skills = models.CharField(max_length=512, help_text='Comma separated skills')
    niche = models.CharField(max_length=100, help_text='e.g. Designer, Prompt maker, Programmer')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Seller Application'
        verbose_name_plural = 'Seller Applications'

    def save(self, *args, **kwargs):
        is_approved = self.status == self.Status.APPROVED
        
        # If the application is already in the database
        if self.pk:
            old_instance = SellerApplication.objects.get(pk=self.pk)
            # If status successfully changed to APPROVED
            if old_instance.status != self.Status.APPROVED and is_approved:
                user = self.user
                user.role = User.Role.SELLER
                user.is_verified = True
                user.is_seller_approved = True
                user.save(update_fields=['role', 'is_verified', 'is_seller_approved'])
        
        # If it's a new instance created as APPROVED
        elif is_approved:
            user = self.user
            user.role = User.Role.SELLER
            user.is_verified = True
            user.is_seller_approved = True
            user.save(update_fields=['role', 'is_verified', 'is_seller_approved'])

        super().save(*args, **kwargs)
