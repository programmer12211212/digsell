from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Coupon

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'ai_limit', 'upload_limit_gb')

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_to', 'active')
