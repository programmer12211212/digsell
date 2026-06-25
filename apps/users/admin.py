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
    list_display = ('user', 'full_name', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    actions = ['approve_applications']

    def approve_applications(self, request, queryset):
        updated = 0
        for app in queryset.filter(status=SellerApplication.Status.PENDING):
            app.status = SellerApplication.Status.APPROVED
            app.save()
            user = app.user
            user.is_seller_approved = True
            # optionally set role
            if user.role != 'SELLER':
                user.role = 'SELLER'
            user.save()
            updated += 1
        self.message_user(request, f'{updated} ariza tasdiqlandi; foydalanuvchilar sotuvchi sifatida belgilandi.')
    approve_applications.short_description = 'Arizalarni tasdiqlash (sotuvchi sifatida belgilash)'
