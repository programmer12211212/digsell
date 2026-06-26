from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, Count
from .models import (
    TelegramProvider, TelegramProductCategory, TelegramProduct,
    TelegramPaymentCard, TelegramOrder, TelegramPayment,
    TelegramGift, TelegramProviderLog, TelegramOrderLog,
    TelegramNotification, TelegramSettings,
    TelegramRewardCampaign, TelegramRewardStage, TelegramRewardClaim
)


class TelegramServicesAdminSite:
    """Admin customization for Telegram Services"""
    pass


# ============================================================================
# TELEGRAM PROVIDER ADMIN
# ============================================================================

@admin.register(TelegramProvider)
class TelegramProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'status_badge', 'balance_display', 'test_mode_badge', 'created_at']
    list_filter = ['is_active', 'is_test', 'name', 'created_at']
    search_fields = ['name', 'api_token']
    readonly_fields = ['created_at', 'updated_at', 'balance_display']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'is_active', 'is_test')
        }),
        ('API Configuration', {
            'fields': ('api_token', 'wallet_version', 'payment_method')
        }),
        ('Balance Information', {
            'fields': ('balance', 'stars_balance', 'premium_balance', 'balance_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'
    
    def test_mode_badge(self, obj):
        if obj.is_test:
            return format_html('<span style="color: orange; font-weight: bold;">TEST MODE</span>')
        return format_html('<span style="color: green;">PRODUCTION</span>')
    test_mode_badge.short_description = 'Mode'
    
    def balance_display(self, obj):
        bal_str = f"{obj.balance:,.2f}"
        stars_str = f"{obj.stars_balance:,.2f}"
        prem_str = f"{obj.premium_balance:,.2f}"
        return format_html(
            '<strong>{}</strong> UZS (⭐ {} / 💎 {})',
            bal_str, stars_str, prem_str
        )
    balance_display.short_description = 'Current Balance'


# ============================================================================
# PRODUCT CATEGORY ADMIN
# ============================================================================

@admin.register(TelegramProductCategory)
class TelegramProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'icon', 'image_preview', 'name', 'product_count']
    list_filter = ['name']
    search_fields = ['name', 'display_name']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Display', {
            'fields': ('icon', 'color', 'image')
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        return format_html(
            '<strong style="color: blue;">{}</strong>',
            count
        )
    product_count.short_description = 'Products'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 40px; border-radius: 8px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


# ============================================================================
# PRODUCT ADMIN
# ============================================================================

@admin.register(TelegramProduct)
class TelegramProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rarity_badge', 'price_display', 'price_stars', 'stock_display', 'status_badge', 'featured_badge', 'created_at']
    list_filter = ['category', 'rarity', 'is_resale', 'status', 'is_featured', 'created_at']
    search_fields = ['name', 'sku', 'description']
    autocomplete_fields = ['category', 'provider']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'sku')
        }),
        ('Product Details', {
            'fields': ('quantity', 'unit', 'icon', 'image')
        }),
        ('Pricing', {
            'fields': ('price_uzs', 'price_stars', 'price_usd')
        }),
        ('Marketplace Attributes', {
            'fields': ('rarity', 'is_resale')
        }),
        ('Inventory & Status', {
            'fields': ('status', 'stock', 'is_featured')
        }),
        ('Delivery Configuration', {
            'fields': ('auto_delivery', 'delivery_type', 'delivery_api_method', 'provider'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        price_str = f"{obj.price_uzs:,.0f}"
        return format_html(
            '<strong style="color: green;">{}</strong> UZS',
            price_str
        )
    price_display.short_description = 'Price'
    
    def stock_display(self, obj):
        if obj.stock == -1:
            return format_html('<span style="color: blue;">Unlimited</span>')
        color = 'green' if obj.stock > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.stock
        )
    stock_display.short_description = 'Stock'
    
    def status_badge(self, obj):
        colors = {'active': 'green', 'inactive': 'orange', 'discontinued': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: gold; font-weight: bold;">⭐ Featured</span>')
        return '-'
    featured_badge.short_description = 'Featured'

    def rarity_badge(self, obj):
        if not obj.rarity:
            return "-"
        colors = {
            'common': '#94a3b8',
            'rare': '#3b82f6',
            'epic': '#a855f7',
            'legendary': '#f59e0b',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.rarity, '#94a3b8'), obj.get_rarity_display()
        )
    rarity_badge.short_description = 'Rarity'


# ============================================================================
# PAYMENT CARD ADMIN
# ============================================================================

@admin.register(TelegramPaymentCard)
class TelegramPaymentCardAdmin(admin.ModelAdmin):
    list_display = ['card_display', 'bank_name', 'active_badge', 'created_at']
    list_filter = ['is_active', 'bank_name', 'created_at']
    search_fields = ['card_holder', 'bank_name', 'card_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'card_holder', 'bank_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def card_display(self, obj):
        masked = '*' * 12 + obj.card_number[-4:]
        return format_html(
            '<strong>{}</strong>',
            masked
        )
    card_display.short_description = 'Card Number'
    
    def active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    active_badge.short_description = 'Status'


# ============================================================================
# TELEGRAM ORDER ADMIN
# ============================================================================

@admin.register(TelegramOrder)
class TelegramOrderAdmin(admin.ModelAdmin):
    list_display = ['unique_code', 'user', 'product_name', 'amount_display', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at', 'product__category']
    search_fields = ['unique_code', 'telegram_username', 'user__username']
    readonly_fields = ['unique_code', 'created_at', 'updated_at', 'user_display', 'order_logs_display']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('unique_code', 'user', 'product', 'status')
        }),
        ('Telegram User', {
            'fields': ('telegram_username', 'telegram_user_id', 'telegram_avatar')
        }),
        ('Payment Details', {
            'fields': ('base_price', 'unique_amount', 'payment_method', 'payment_card')
        }),
        ('Delivery Information', {
            'fields': ('transaction_id', 'delivery_attempts', 'provider_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'payment_confirmed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Order History', {
            'fields': ('order_logs_display',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_payment_action', 'mark_completed_action', 'retry_delivery_action']
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def amount_display(self, obj):
        formatted_amount = f"{obj.unique_amount:,.0f}"
        return format_html(
            '<strong style="color: green;">{}</strong> UZS',
            formatted_amount
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'new': 'blue',
            'waiting_payment': 'orange',
            'waiting_confirmation': 'orange',
            'paid': 'blue',
            'processing': 'cyan',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def user_display(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id, obj.user.get_full_name() or obj.user.username
        )
    user_display.short_description = 'User'
    
    def order_logs_display(self, obj):
        logs = obj.logs.all()[:10]
        html = '<ul>'
        for log in logs:
            html += f'<li>{log.created_at.strftime("%Y-%m-%d %H:%M")} - {log.action}: {log.message}</li>'
        html += '</ul>'
        return format_html(html)
    order_logs_display.short_description = 'Recent Logs'
    
    def confirm_payment_action(self, request, queryset):
        from .services import TelegramOrderService
        confirmed = 0
        for order in queryset.filter(status='waiting_confirmation'):
            if TelegramOrderService.confirm_payment(order, request.user):
                confirmed += 1
        self.message_user(request, f'{confirmed} orders payment confirmed')
    confirm_payment_action.short_description = 'Confirm payment for selected orders'
    
    def mark_completed_action(self, request, queryset):
        from .services import TelegramOrderService
        completed = 0
        for order in queryset.filter(status__in=['paid', 'processing']):
            if TelegramOrderService.complete_order(order):
                completed += 1
        self.message_user(request, f'{completed} orders marked as completed')
    mark_completed_action.short_description = 'Mark as completed'
    
    def retry_delivery_action(self, request, queryset):
        from .services import TelegramOrderService
        retried = 0
        for order in queryset.filter(status='paid'):
            if TelegramOrderService.process_delivery(order):
                retried += 1
        self.message_user(request, f'{retried} delivery retries initiated')
    retry_delivery_action.short_description = 'Retry delivery'


# ============================================================================
# TELEGRAM PAYMENT ADMIN
# ============================================================================

@admin.register(TelegramPayment)
class TelegramPaymentAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'amount_display', 'payment_status_badge', 'payment_method', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['order__unique_code']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'amount', 'currency', 'payment_method')
        }),
        ('Status', {
            'fields': ('payment_status',)
        }),
        ('Confirmation', {
            'fields': ('confirmed_by', 'confirmation_note', 'confirmed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_code(self, obj):
        return obj.order.unique_code
    order_code.short_description = 'Order Code'
    
    def amount_display(self, obj):
        amount_str = f"{obj.amount:,.0f}"
        return format_html(
            '<strong style="color: green;">{}</strong> {}',
            amount_str, obj.currency
        )
    amount_display.short_description = 'Amount'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'failed': 'red',
            'refunded': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.payment_status, 'gray'), obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Status'


# ============================================================================
# TELEGRAM GIFT ADMIN
# ============================================================================

@admin.register(TelegramGift)
class TelegramGiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_display', 'active_badge', 'provider', 'created_at']
    list_filter = ['is_active', 'provider', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Gift Information', {
            'fields': ('name', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('price_uzs',)
        }),
        ('Provider Configuration', {
            'fields': ('provider', 'provider_gift_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        price_str = f"{obj.price_uzs:,.0f}"
        return format_html(
            '<strong style="color: green;">{}</strong> UZS',
            price_str
        )
    price_display.short_description = 'Price'
    
    def active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    active_badge.short_description = 'Status'


# ============================================================================
# PROVIDER LOG ADMIN
# ============================================================================

@admin.register(TelegramProviderLog)
class TelegramProviderLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'provider', 'status_badge', 'created_at']
    list_filter = ['provider', 'method', 'status_code', 'created_at']
    search_fields = ['method', 'endpoint']
    readonly_fields = ['created_at', 'request_data_display', 'response_data_display']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('provider', 'method', 'endpoint')
        }),
        ('Data', {
            'fields': ('request_data_display', 'response_data_display')
        }),
        ('Status', {
            'fields': ('status_code', 'error')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.status_code == 200:
            color = 'green'
        elif 400 <= obj.status_code < 500:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status_code or 'ERROR'
        )
    status_badge.short_description = 'Status'
    
    def request_data_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.request_data, indent=2))
    request_data_display.short_description = 'Request Data'
    
    def response_data_display(self, obj):
        if not obj.response_data:
            return '-'
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.response_data, indent=2))
    response_data_display.short_description = 'Response Data'


# ============================================================================
# NOTIFICATION ADMIN
# ============================================================================

@admin.register(TelegramNotification)
class TelegramNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type_badge', 'read_badge', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'order', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def type_badge(self, obj):
        colors = {
            'order_created': 'blue',
            'payment_pending': 'orange',
            'payment_confirmed': 'green',
            'delivery_processing': 'cyan',
            'delivery_completed': 'green',
            'delivery_failed': 'red',
            'refund_issued': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.notification_type, 'gray'), obj.get_notification_type_display()
        )
    type_badge.short_description = 'Type'
    
    def read_badge(self, obj):
        status = '✓ Read' if obj.is_read else 'Unread'
        color = 'gray' if obj.is_read else 'blue'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    read_badge.short_description = 'Status'


# ============================================================================
# REWARD TRACK ADMIN
# ============================================================================

class TelegramRewardStageInline(admin.TabularInline):
    model = TelegramRewardStage
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['position', 'title', 'target_type', 'target_value', 'reward_type', 'reward_amount', 'is_active']


@admin.register(TelegramRewardCampaign)
class TelegramRewardCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'start_date', 'end_date', 'stage_count', 'created_at']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TelegramRewardStageInline]
    fieldsets = (
        ('Campaign Details', {
            'fields': ('name', 'description', 'highlight_text', 'image', 'is_active')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def stage_count(self, obj):
        return obj.stages.count()
    stage_count.short_description = 'Stages'


@admin.register(TelegramRewardStage)
class TelegramRewardStageAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'position', 'title', 'target_summary', 'reward_summary', 'is_active']
    list_filter = ['campaign', 'target_type', 'reward_type', 'is_active']
    search_fields = ['title', 'description', 'reward_description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Stage Basics', {
            'fields': ('campaign', 'position', 'title', 'description', 'is_active')
        }),
        ('Reward Target', {
            'fields': ('target_type', 'target_value')
        }),
        ('Reward Details', {
            'fields': ('reward_type', 'reward_amount', 'reward_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def target_summary(self, obj):
        return obj.target_label
    target_summary.short_description = 'Target'

    def reward_summary(self, obj):
        return obj.reward_label
    reward_summary.short_description = 'Reward'


@admin.register(TelegramRewardClaim)
class TelegramRewardClaimAdmin(admin.ModelAdmin):
    list_display = ['user', 'campaign', 'stage', 'status', 'reward_summary', 'admin_note', 'reward_granted', 'requested_at']
    list_filter = ['status', 'campaign', 'stage', 'reward_type', 'reward_granted']
    search_fields = ['user__username', 'stage__title', 'campaign__name', 'admin_note']
    readonly_fields = ['requested_at', 'processed_at']
    actions = ['approve_claim_action', 'deny_claim_action']
    fieldsets = (
        ('Claim Information', {
            'fields': ('user', 'campaign', 'stage', 'status', 'reward_type', 'reward_amount', 'reward_description', 'reward_granted')
        }),
        ('Processing', {
            'fields': ('admin_note', 'processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('requested_at',),
            'classes': ('collapse',)
        }),
    )

    def reward_summary(self, obj):
        if obj.reward_type == 'bonus_balance':
            return f"Bonus {int(obj.reward_amount):,} UZS"
        if obj.reward_type == 'cashback':
            return f"Cashback {int(obj.reward_amount):,} UZS"
        if obj.reward_type == 'bonus_points':
            return f"{int(obj.reward_amount):,} points"
        return obj.reward_description or obj.reward_type
    reward_summary.short_description = 'Reward'

    def approve_claim_action(self, request, queryset):
        from .services import TelegramRewardService
        approved = 0
        for claim in queryset.filter(status=TelegramRewardClaim.ClaimStatus.PENDING):
            if TelegramRewardService.approve_reward_claim(claim, request.user):
                approved += 1
        self.message_user(request, f'{approved} reward claims approved.')
    approve_claim_action.short_description = 'Approve selected reward claims'

    def deny_claim_action(self, request, queryset):
        denied = queryset.filter(status=TelegramRewardClaim.ClaimStatus.PENDING).update(
            status=TelegramRewardClaim.ClaimStatus.DENIED,
            processed_at=timezone.now(),
            processed_by=request.user
        )
        self.message_user(request, f'{denied} reward claims denied.')
    deny_claim_action.short_description = 'Deny selected reward claims'


# ============================================================================
# SETTINGS ADMIN
# ============================================================================

@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Service Status', {
            'fields': ('service_enabled',)
        }),
        ('Payment Configuration', {
            'fields': ('min_order_amount', 'max_order_amount', 'payment_confirmation_timeout')
        }),
        ('Delivery Configuration', {
            'fields': ('auto_delivery_enabled', 'max_delivery_retries', 'delivery_retry_interval')
        }),
        ('Fees', {
            'fields': ('commission_percentage',)
        }),
        ('Support Information', {
            'fields': ('support_email', 'support_telegram')
        }),
        ('Gift Sales Settings', {
            'fields': ('gifts_telegram_username', 'gifts_message_template', 'gifts_redirect_enabled')
        }),
    )
    
    def has_add_permission(self, request):
        return not TelegramSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================================
# CUSTOM ADMIN URLS & DASHBOARD VIEW
# ============================================================================

def telegram_dashboard_view(request):
    from django.shortcuts import render
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models.functions import TruncDay
    
    # Total stats
    total_orders = TelegramOrder.objects.count()
    completed_orders = TelegramOrder.objects.filter(status='completed')
    total_revenue = completed_orders.aggregate(total=Sum('unique_amount'))['total'] or 0
    success_count = completed_orders.count()
    
    success_rate = (success_count / total_orders * 100) if total_orders > 0 else 0
    
    pending_orders_count = TelegramOrder.objects.filter(
        status__in=['new', 'waiting_payment', 'waiting_confirmation', 'processing']
    ).count()
    
    # Categories distribution
    category_data = TelegramOrder.objects.filter(status='completed').values(
        'product__category__display_name'
    ).annotate(
        revenue=Sum('unique_amount'),
        count=Count('id')
    )
    
    category_labels = [item['product__category__display_name'] for item in category_data if item['product__category__display_name']]
    category_revenues = [float(item['revenue']) for item in category_data]
    category_counts = [item['count'] for item in category_data]
    
    # Daily sales for last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_sales = TelegramOrder.objects.filter(
        status='completed',
        created_at__gte=thirty_days_ago
    ).annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        revenue=Sum('unique_amount'),
        count=Count('id')
    ).order_by('day')
    
    daily_labels = [item['day'].strftime('%Y-%m-%d') for item in daily_sales]
    daily_revenues = [float(item['revenue']) for item in daily_sales]
    daily_counts = [item['count'] for item in daily_sales]
    
    # Provider statistics
    providers = TelegramProvider.objects.all()
    provider_stats = []
    for prov in providers:
        logs = TelegramProviderLog.objects.filter(provider=prov).order_by('-created_at')[:10]
        total_prov_logs = TelegramProviderLog.objects.filter(provider=prov).count()
        success_prov_logs = TelegramProviderLog.objects.filter(provider=prov, status_code=200).count()
        prov_success_rate = (success_prov_logs / total_prov_logs * 100) if total_prov_logs > 0 else 100.0
        
        provider_stats.append({
            'provider': prov,
            'success_rate': prov_success_rate,
            'logs': logs,
            'total_logs': total_prov_logs,
        })
        
    recent_orders = TelegramOrder.objects.order_by('-created_at')[:10]
    
    context = {
        **admin.site.each_context(request),
        'title': 'Telegram Xizmatlari Dashboard',
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'success_count': success_count,
        'success_rate': success_rate,
        'pending_orders_count': pending_orders_count,
        
        'category_labels': category_labels,
        'category_revenues': category_revenues,
        'category_counts': category_counts,
        
        'daily_labels': daily_labels,
        'daily_revenues': daily_revenues,
        'daily_counts': daily_counts,
        
        'provider_stats': provider_stats,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin/telegram_services/dashboard.html', context)


# Hooking custom url into admin site
original_get_urls = admin.site.get_urls
def new_get_urls():
    from django.urls import path
    urls = original_get_urls()
    custom_urls = [
        path('telegram-services/dashboard/', admin.site.admin_view(telegram_dashboard_view), name='admin_telegram_dashboard'),
    ]
    return custom_urls + urls
admin.site.get_urls = new_get_urls
