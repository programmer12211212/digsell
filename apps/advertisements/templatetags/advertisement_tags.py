"""
Template tags for rendering advertisements.
Provides tags for displaying different banner types dynamically.
"""
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Q
from apps.advertisements.models import Advertisement, BannerGroup

register = template.Library()


@register.inclusion_tag('advertisements/hero_slider.html')
def hero_slider(position='hero', device_target='all'):
    """
    Render hero slider banner group.
    Usage: {% hero_slider position="hero" %}
    """
    group = BannerGroup.objects.filter(
        status='active',
        banner_type='hero_slider',
        position=position
    ).first()
    
    if not group:
        return {'banners': []}
    
    now = timezone.now()
    banners = group.banners.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        status='active'
    ).order_by('-priority', 'display_order')
    
    return {
        'group': group,
        'banners': banners,
        'device_target': device_target,
    }


@register.inclusion_tag('advertisements/promotion_banner.html')
def promotion_banner(position='above_content'):
    """
    Render promotion banner.
    Usage: {% promotion_banner position="above_content" %}
    """
    now = timezone.now()
    banner = Advertisement.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        banner_type='promotion',
        position=position,
        status='active'
    ).order_by('-priority').first()
    
    return {'banner': banner}


@register.inclusion_tag('advertisements/alert_banner.html')
def alert_banner(position='top'):
    """
    Render alert banner.
    Usage: {% alert_banner position="top" %}
    """
    now = timezone.now()
    banner = Advertisement.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        banner_type='alert',
        position=position,
        status='active'
    ).order_by('-priority').first()
    
    return {'banner': banner}


@register.inclusion_tag('advertisements/card_grid.html')
def ad_card_grid(position='below_content', limit=3):
    """
    Render advertisement cards grid.
    Usage: {% ad_card_grid position="below_content" limit=3 %}
    """
    now = timezone.now()
    banners = Advertisement.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        banner_type='card',
        position=position,
        status='active'
    ).order_by('-priority', 'display_order')[:limit]
    
    return {'banners': banners}


@register.inclusion_tag('advertisements/sidebar_banner.html')
def sidebar_banner(position='sidebar_top'):
    """
    Render sidebar banner.
    Usage: {% sidebar_banner position="sidebar_top" %}
    """
    now = timezone.now()
    banner = Advertisement.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        banner_type='sidebar',
        position=position,
        status='active'
    ).order_by('-priority').first()
    
    return {'banner': banner}


@register.inclusion_tag('advertisements/carousel.html')
def ad_carousel(banner_type='carousel', position='inline_content'):
    """
    Render advertisement carousel.
    Usage: {% ad_carousel banner_type="carousel" %}
    """
    group = BannerGroup.objects.filter(
        status='active',
        banner_type=banner_type,
        position=position
    ).first()
    
    if not group:
        return {'banners': []}
    
    now = timezone.now()
    banners = group.banners.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        status='active'
    ).order_by('-priority', 'display_order')
    
    return {
        'group': group,
        'banners': banners,
    }


@register.inclusion_tag('advertisements/discount_banner.html')
def discount_banner(position='above_content'):
    """
    Render discount banner.
    Usage: {% discount_banner %}
    """
    now = timezone.now()
    banner = Advertisement.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
        banner_type='discount',
        position=position,
        status='active'
    ).order_by('-priority').first()
    
    return {'banner': banner}


@register.filter
def get_device_css(device_target):
    """
    Get CSS class for device targeting.
    Usage: {{ banner.device_target|get_device_css }}
    """
    device_classes = {
        'all': '',
        'desktop': 'hidden lg:block',
        'tablet': 'hidden md:block lg:hidden',
        'mobile': 'block md:hidden',
        'mobile_tablet': 'block lg:hidden',
        'desktop_tablet': 'hidden md:block',
    }
    return device_classes.get(device_target, '')


@register.simple_tag
def banner_click_tracker(ad_id):
    """
    Generate click tracking URL.
    Usage: {% banner_click_tracker ad_id %}
    """
    from django.urls import reverse
    return reverse('advertisements:record_click', kwargs={'ad_id': ad_id})


@register.simple_tag
def banner_impression_tracker(ad_id):
    """
    Generate impression tracking URL.
    Usage: {% banner_impression_tracker ad_id %}
    """
    from django.urls import reverse
    return reverse('advertisements:record_impression', kwargs={'ad_id': ad_id})
