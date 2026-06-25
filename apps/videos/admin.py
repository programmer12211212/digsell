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
    list_display = ('title', 'product_type', 'seller', 'category', 'price', 'is_active')
    list_filter = ('product_type', 'is_active', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [DigitalFileInline]

@admin.register(VideoPurchase)
class VideoPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'purchased_at')
