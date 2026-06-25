from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class BonusRule(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Xariddan beriladigan bonus foizi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

class DailyBonus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kunlik bonus"
        verbose_name_plural = "Kunlik bonuslar"

class SpinWheelPrize(models.Model):
    class PrizeType(models.TextChoices):
        BONUS = "BONUS", "Bonus pul"
        CASHBACK = "CASHBACK", "Extra Cashback"
        PROMO = "PROMO", "Promokod"
        FREE_VIDEO = "FREE_VIDEO", "Bepul video"
        NONE = "NONE", "Yana bir bor urinib ko'ring"

    name = models.CharField(max_length=100)
    prize_type = models.CharField(max_length=20, choices=PrizeType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="marketing/prizes/", blank=True, null=True)
    probability = models.FloatField(help_text="Sovrin chiqish ehtimoli (0-100)")

    def __str__(self):
        return self.name

class SpinWheelLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prize = models.ForeignKey(SpinWheelPrize, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Competition(models.Model):
    class Type(models.TextChoices):
        TOP_BUYER = "TOP_BUYER", "Top Xaridor"
        TOP_SELLER = "TOP_SELLER", "Top Sotuvchi"
        TOP_REFERRAL = "TOP_REFERRAL", "Top Referral"
        TOP_SPENDER = "TOP_SPENDER", "Top Spender"

    title = models.CharField(max_length=255)
    description = models.TextField()
    comp_type = models.CharField(max_length=20, choices=Type.choices)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Reward(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="rewards")
    rank = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    prize_amount = models.DecimalField(max_digits=15, decimal_places=2)
    image = models.ImageField(upload_to="marketing/rewards/")
    
    def __str__(self):
        return f"{self.competition.title} - Rank {self.rank}"

class Banner(models.Model):
    class BannerType(models.TextChoices):
        WEB = "WEB", "Web"
        MOBILE = "MOBILE", "Mobil"
        SLIDER = "SLIDER", "Slider"

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="banners/")
    link_url = models.CharField(max_length=500, blank=True)
    banner_type = models.CharField(max_length=20, choices=BannerType.choices, default=BannerType.SLIDER)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Advertisement(models.Model):
    class AdType(models.TextChoices):
        BANNER = "BANNER", "Banner"
        CARD = "CARD", "Reklama karta"
        POPUP = "POPUP", "Popup"

    class Placement(models.TextChoices):
        HOME = "HOME", "Bosh sahifa"
        MARKETPLACE = "MARKETPLACE", "Marketplace"
        COURSES = "COURSES", "Video kurslar"
        SIDEBAR = "SIDEBAR", "Yon panel"
        GLOBAL = "GLOBAL", "Barcha sahifalar"

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to="ads/", blank=True, null=True)
    link_url = models.CharField(max_length=500, blank=True)
    ad_type = models.CharField(max_length=20, choices=AdType.choices, default=AdType.CARD)
    placement = models.CharField(max_length=20, choices=Placement.choices, default=Placement.GLOBAL)
    bg_color = models.CharField(max_length=20, blank=True, default="#0ea5e9")
    text_color = models.CharField(max_length=20, blank=True, default="#ffffff")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_from = models.DateTimeField(null=True, blank=True)
    show_until = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Reklama"
        verbose_name_plural = "Reklamalar"

    def __str__(self):
        return f"{self.title} ({self.get_ad_type_display()})"

    @property
    def is_visible_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.show_from and now < self.show_from:
            return False
        if self.show_until and now > self.show_until:
            return False
        return True


class Promocode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
