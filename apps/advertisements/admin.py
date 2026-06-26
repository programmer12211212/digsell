"""
Django Admin interface for Advertisement management.
Fully featured CRUD with preview, scheduling, and targeting.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q
from .models import (
    Advertisement, BannerGroup, AdvertisementClick, AdvertisementImpression
)


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        'title_with_type', 'position', 'status_badge', 
        'device_target', 'priority', 'impressions_display', 'actions_display'
    )
    list_filter = (
        'status', 'banner_type', 'position', 'device_target',
        'alert_type', 'created_at', 'start_date', 'end_date'
    )
    search_fields = ('title', 'heading', 'subheading', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at', 'current_impressions', 'preview_image')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'banner_type', 'position')
        }),
        ('Content', {
            'fields': ('heading', 'subheading', 'content', 'preview_image'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('image', 'mobile_image', 'thumbnail'),
            'classes': ('collapse',)
        }),
        ('CTA Button', {
            'fields': ('cta_text', 'cta_url', 'cta_target_blank'),
            'classes': ('collapse',)
        }),
        ('Styling & Animation', {
            'fields': (
                'background_color', 'gradient', 'text_color',
                'animation_style', 'animation_duration'
            ),
            'classes': ('collapse',)
        }),
        ('Alert Configuration', {
            'fields': ('alert_type', 'is_closable'),
            'classes': ('collapse',)
        }),
        ('Promotion Configuration', {
            'fields': ('discount_label', 'has_countdown', 'countdown_text'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'max_impressions', 'current_impressions')
        }),
        ('Targeting & Priority', {
            'fields': (
                'device_target', 'target_category', 'target_product',
                'priority', 'display_order'
            )
        }),
        ('Status', {
            'fields': ('status', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_with_type(self, obj):
        """Display title with banner type badge."""
        type_colors = {
            'hero_slider': '#3b82f6',
            'promotion': '#ec4899',
            'card': '#06b6d4',
            'alert': '#f59e0b',
            'carousel': '#8b5cf6',
            'sidebar': '#10b981',
            'category': '#6366f1',
            'product': '#14b8a6',
            'marketplace': '#0891b2',
        }
        color = type_colors.get(obj.banner_type, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span> <small style="color: #999;">({})</small>',
            color,
            obj.title,
            obj.get_banner_type_display()
        )
    title_with_type.short_description = 'Title'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'active': '#10b981',
            'draft': '#6b7280',
            'inactive': '#ef4444',
            'archived': '#9ca3af',
        }
        color = colors.get(obj.status, '#6b7280')
        is_scheduled = obj.start_date and obj.start_date > timezone.now()
        badge_text = obj.get_status_display()
        if is_scheduled:
            badge_text += ' (Scheduled)'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color,
            badge_text
        )
    status_badge.short_description = 'Status'
    
    def impressions_display(self, obj):
        """Display impression count with max."""
        if obj.max_impressions:
            percentage = (obj.current_impressions / obj.max_impressions) * 100
            color = '#10b981' if percentage < 80 else '#f59e0b' if percentage < 100 else '#ef4444'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{}</span>',
                color,
                obj.current_impressions,
                obj.max_impressions
            )
        return format_html(
            '<span style="color: #6b7280;">{} (unlimited)</span>',
            obj.current_impressions
        )
    impressions_display.short_description = 'Impressions'
    
    def actions_display(self, obj):
        """Display quick actions."""
        actions = []
        if obj.status != Advertisement.Status.ACTIVE:
            actions.append('<a style="color: #3b82f6; text-decoration: none;" href="#" onclick="return false;">Activate</a>')
        if obj.status == Advertisement.Status.ACTIVE:
            actions.append('<a style="color: #ef4444; text-decoration: none;" href="#" onclick="return false;">Deactivate</a>')
        return format_html(' | '.join(actions) if actions else '<span style="color: #9ca3af;">-</span>')
    actions_display.short_description = 'Actions'
    
    def preview_image(self, obj):
        """Preview image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 300px; border-radius: 8px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #9ca3af;">No image uploaded</span>')
    preview_image.short_description = 'Image Preview'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on save."""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize query."""
        qs = super().get_queryset(request)
        return qs.select_related('target_category', 'target_product', 'created_by')


class AdvertisementInline(admin.TabularInline):
    """Inline display of banners in group admin."""
    model = BannerGroup.banners.through
    extra = 1


@admin.register(BannerGroup)
class BannerGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'banner_type_badge', 'position',
        'banner_count', 'status_badge', 'carousel_settings'
    )
    list_filter = ('banner_type', 'position', 'status', 'autoplay')
    search_fields = ('name', 'description')
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Group Information', {
            'fields': ('id', 'name', 'description', 'banner_type', 'position', 'status')
        }),
        ('Carousel/Slider Settings', {
            'fields': (
                'autoplay', 'autoplay_delay', 'loop_enabled',
                'show_navigation', 'show_indicators', 'animation_duration'
            )
        }),
        ('Banners', {
            'fields': ('banners',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('banners',)
    
    def banner_type_badge(self, obj):
        """Display banner type as badge."""
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            obj.get_banner_type_display()
        )
    banner_type_badge.short_description = 'Type'
    
    def banner_count(self, obj):
        """Display count of banners in group."""
        count = obj.banners.count()
        return format_html(
            '<span style="background-color: #e5e7eb; color: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;">{} banner{}</span>',
            count,
            's' if count != 1 else ''
        )
    banner_count.short_description = 'Banners'
    
    def status_badge(self, obj):
        """Display status."""
        colors = {
            'active': '#10b981',
            'draft': '#6b7280',
            'inactive': '#ef4444',
            'archived': '#9ca3af',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def carousel_settings(self, obj):
        """Display carousel settings as text."""
        settings = []
        if obj.autoplay:
            settings.append(f'Auto ({obj.autoplay_delay}ms)')
        if obj.loop_enabled:
            settings.append('Loop')
        if obj.show_navigation:
            settings.append('Nav')
        if obj.show_indicators:
            settings.append('Indicators')
        return ' • '.join(settings) if settings else 'No settings'
    carousel_settings.short_description = 'Carousel'


@admin.register(AdvertisementClick)
class AdvertisementClickAdmin(admin.ModelAdmin):
    list_display = ('advertisement', 'clicked_at', 'user', 'user_ip')
    list_filter = ('advertisement', 'clicked_at', 'user')
    search_fields = ('advertisement__title', 'user__username', 'user_ip')
    readonly_fields = ('advertisement', 'clicked_at', 'user', 'user_ip', 'user_agent')
    
    def has_add_permission(self, request):
        """Prevent manual addition of clicks."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of click data."""
        return False


@admin.register(AdvertisementImpression)
class AdvertisementImpressionAdmin(admin.ModelAdmin):
    list_display = ('advertisement', 'viewed_at', 'user', 'user_ip', 'device')
    list_filter = ('advertisement', 'viewed_at', 'device')
    search_fields = ('advertisement__title', 'user__username', 'user_ip')
    readonly_fields = ('advertisement', 'viewed_at', 'user', 'user_ip', 'device')
    
    def has_add_permission(self, request):
        """Prevent manual addition of impressions."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of impression data."""
        return False
