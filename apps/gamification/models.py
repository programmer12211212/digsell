from django.db import models
from django.conf import settings
from decimal import Decimal

class BonusRule(models.Model):
    name = models.CharField(max_length=100)
    bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0) # 1% cashback etc
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.bonus_percentage}%)"

class Competition(models.Model):
    class Type(models.TextChoices):
        TOP_BUYER = 'BUYER', 'Eng ko\'p xarid qilgan'
        TOP_SELLER = 'SELLER', 'Eng ko\'p sotgan'
        TOP_REFERRAL = 'REFERRAL', 'Eng ko\'p referral chaqirgan'

    title = models.CharField(max_length=200)
    comp_type = models.CharField(max_length=20, choices=Type.choices)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    prize_pool = models.JSONField(default=dict) # e.g. {"1": 1000000, "2": 500000}
    
    is_finished = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.get_comp_type_display()})"

class SpinWheelPrize(models.Model):
    title = models.CharField(max_length=100)
    prize_type = models.CharField(max_length=20, choices=[
        ('BONUS', 'Bonus Points'),
        ('BALANCE', 'Wallet Balance'),
        ('PROMO', 'Promo Code'),
        ('FREE_VIDEO', 'Free Video Access')
    ])
    value = models.CharField(max_length=50) # Point amount or Promo ID
    probability = models.DecimalField(max_digits=5, decimal_places=2) # e.g. 5.00 for 5%
    
    def __str__(self):
        return self.title

class UserBonusLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
