from django.contrib import admin
from .models import CourseCategory, Video, DigitalFile, VideoPurchase

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}

class DigitalFileInline(admin.TabularInline):
    model = DigitalFile
    extra = 1

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'product_type', 'seller', 'category', 'price', 'is_active', 'moderation_status'
    )
    list_filter = ('product_type', 'moderation_status', 'is_active', 'category')
    search_fields = ('title', 'description', 'tags', 'seller__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [DigitalFileInline]
    actions = ['approve_products', 'reject_products', 'request_changes', 'suspend_products']

    def approve_products(self, request, queryset):
        updated = 0
        for product in queryset:
            product.moderation_status = Video.ModerationStatus.APPROVED
            product.is_active = True
            product.moderation_feedback = ''
            product.save()
            updated += 1
        self.message_user(request, f'{updated} mahsulot tasdiqlandi va sotuvga chiqdi.')
    approve_products.short_description = 'Mahsulotlarni tasdiqlash va sotuvga chiqarish'

    def reject_products(self, request, queryset):
        updated = 0
        for product in queryset:
            product.moderation_status = Video.ModerationStatus.REJECTED
            product.is_active = False
            product.save()
            updated += 1
        self.message_user(request, f'{updated} mahsulot rad etildi.')
    reject_products.short_description = 'Mahsulotlarni rad etish'

    def request_changes(self, request, queryset):
        updated = 0
        for product in queryset:
            product.moderation_status = Video.ModerationStatus.CHANGES_REQUESTED
            product.is_active = False
            product.save()
            updated += 1
        self.message_user(request, f'{updated} mahsulot uchun o‘zgarishlar talab qilindi.')
    request_changes.short_description = 'Mahsulotlar uchun o‘zgarishlar talab qilish'

    def suspend_products(self, request, queryset):
        updated = 0
        for product in queryset:
            product.moderation_status = Video.ModerationStatus.SUSPENDED
            product.is_active = False
            product.save()
            updated += 1
        self.message_user(request, f'{updated} mahsulot vaqtincha to‘xtatildi.')
    suspend_products.short_description = 'Mahsulotlarni suspend qilish'

@admin.register(VideoPurchase)
class VideoPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'purchased_at')
