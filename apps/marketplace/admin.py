from django.contrib import admin
from .models import Category, Product, ProductFile, Wishlist

class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'price', 'sale_price', 'featured', 'popular', 'is_active', 'is_verified')
    list_filter = ('product_type', 'featured', 'popular', 'is_active', 'is_verified', 'category')
    search_fields = ('title', 'description', 'short_description', 'tags', 'seo_title', 'seller__email')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductFileInline]
    actions = ['approve_products']

    def approve_products(self, request, queryset):
        updated = queryset.update(is_verified=True, is_active=True)
        self.message_user(request, f'{updated} mahsulot tasdiqlandi va sotuvga qo‘yildi.')
    approve_products.short_description = 'Tasdiqlash va sotuvga chiqarish'

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__title')
