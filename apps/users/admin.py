from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Wallet, WalletTransaction
from .models import SellerApplication

@admin.register(User)
class EnterpriseUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'loyalty_level', 'is_verified')
    list_filter = ('role', 'loyalty_level', 'is_verified')
    fieldsets = UserAdmin.fieldsets + (
        ('Enterprise Data', {'fields': ('phone', 'role', 'loyalty_level', 'avatar', 'telegram_id', 'referred_by', 'referral_code', 'is_verified')}),
    )

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'bonus_points', 'cashback_balance')
    search_fields = ('user__username',)

@admin.register(WalletTransaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'tx_type', 'reason', 'created_at')
    list_filter = ('tx_type', 'created_at')


@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'full_name', 'phone', 'telegram_username', 'status', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'country', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'phone', 'telegram_username', 'email', 'skills', 'niche')
    actions = [
        'approve_applications',
        'reject_applications',
        'request_changes',
        'suspend_sellers',
        'ban_sellers',
    ]

    def approve_applications(self, request, queryset):
        updated = 0
        for app in queryset.exclude(status=SellerApplication.Status.APPROVED):
            app.status = SellerApplication.Status.APPROVED
            app.admin_note = ''
            app.save()
            updated += 1
        self.message_user(request, f'{updated} ariza tasdiqlandi; foydalanuvchilar sotuvchi sifatida belgilandi.')
    approve_applications.short_description = 'Arizalarni tasdiqlash (sotuvchi sifatida belgilash)'

    def reject_applications(self, request, queryset):
        updated = 0
        for app in queryset.exclude(status=SellerApplication.Status.REJECTED):
            app.status = SellerApplication.Status.REJECTED
            app.save()
            updated += 1
        self.message_user(request, f'{updated} ariza rad etildi.')
    reject_applications.short_description = 'Arizalarni rad etish'

    def request_changes(self, request, queryset):
        updated = 0
        for app in queryset.exclude(status=SellerApplication.Status.CHANGES_REQUESTED):
            app.status = SellerApplication.Status.CHANGES_REQUESTED
            app.save()
            updated += 1
        self.message_user(request, f'{updated} ariza uchun o‘zgarishlar talab qilindi.')
    request_changes.short_description = 'O‘zgarishlar talab qilish'

    def suspend_sellers(self, request, queryset):
        updated = 0
        for app in queryset.exclude(status=SellerApplication.Status.SUSPENDED):
            app.status = SellerApplication.Status.SUSPENDED
            app.save()
            updated += 1
        self.message_user(request, f'{updated} sotuvchi vaqtincha suspend qilindi.')
    suspend_sellers.short_description = 'Sotuvchilarni suspend qilish'

    def ban_sellers(self, request, queryset):
        updated = 0
        for app in queryset.exclude(status=SellerApplication.Status.BANNED):
            app.status = SellerApplication.Status.BANNED
            app.save()
            updated += 1
        self.message_user(request, f'{updated} sotuvchi ban qilindi.')
    ban_sellers.short_description = 'Sotuvchilarni ban qilish'
