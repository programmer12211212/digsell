from django.contrib import admin
from .models import Order, OrderItem, Coupon, Cart, CartItem
from apps.marketplace.views import _complete_order

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price_at_purchase')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'final_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('buyer__username', 'transaction_id')
    inlines = [OrderItemInline]
    
    actions = ['mark_as_paid', 'mark_as_completed']

    @admin.action(description="Tanlangan buyurtmalarni To'langan deb belgilash")
    def mark_as_paid(self, request, queryset):
        # For each order, change status and run completion logic to grant purchases and payouts
        for order in queryset:
            old_status = order.status
            if old_status != Order.Status.PAID:
                order.status = Order.Status.PAID
                order.save()
        
    @admin.action(description="Tanlangan buyurtmalarni Yakunlangan deb belgilash")
    def mark_as_completed(self, request, queryset):
        queryset.update(status=Order.Status.COMPLETED)

    def get_search_results(self, request, queryset, search_term):
        try:
            return super().get_search_results(request, queryset, search_term)
        except ValueError:
            # Malformed UUID or similar search parsing error — ignore search term
            return queryset, False

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_purchase')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count_display', 'updated_at')
    inlines = [CartItemInline]

    def item_count_display(self, obj):
        return obj.item_count
    item_count_display.short_description = 'Mahsulotlar'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'times_used', 'valid_to')
    list_filter = ('is_active',)
    search_fields = ('code',)
