from django.contrib import admin
from .models import (
    BonusRule, DailyBonus, SpinWheelPrize, SpinWheelLog,
    Competition, Reward, Promocode, Banner, Advertisement,
)


@admin.register(BonusRule)
class BonusRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'is_active')


@admin.register(DailyBonus)
class DailyBonusAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'claimed_at')
    list_filter = ('claimed_at',)


@admin.register(SpinWheelPrize)
class SpinWheelPrizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'prize_type', 'value', 'probability')


@admin.register(SpinWheelLog)
class SpinWheelLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize', 'created_at')


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'comp_type', 'start_date', 'end_date', 'is_active')


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('title', 'competition', 'rank', 'prize_amount')


@admin.register(Promocode)
class PromocodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'discount_amount', 'is_active', 'used_count')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_type', 'order', 'is_active')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_type', 'placement', 'is_active', 'click_count', 'order')
    list_filter = ('ad_type', 'placement', 'is_active')
