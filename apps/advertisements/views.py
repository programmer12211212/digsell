"""
Views and utilities for advertisement retrieval and rendering.
"""
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Advertisement, BannerGroup, AdvertisementClick, AdvertisementImpression


class AdvertisementService:
    """Service for fetching and filtering advertisements."""
    
    @staticmethod
    def get_active_banners(
        banner_type=None,
        position=None,
        device_target=None,
        category=None,
        product=None,
        limit=None
    ):
        """
        Get active banners matching criteria.
        
        Args:
            banner_type: Filter by banner type (optional)
            position: Filter by display position (optional)
            device_target: Filter by device target (optional)
            category: Filter by category (optional)
            product: Filter by product (optional)
            limit: Max results (optional)
        
        Returns:
            QuerySet of active Advertisement objects
        """
        now = timezone.now()
        
        # Base query: active status with valid schedule
        query = Advertisement.objects.filter(
            status=Advertisement.Status.ACTIVE,
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).exclude(
            max_impressions__lte=models.F('current_impressions')
        )
        
        # Apply filters
        if banner_type:
            query = query.filter(banner_type=banner_type)
        
        if position:
            query = query.filter(position=position)
        
        if device_target:
            query = query.filter(device_target=device_target)
        
        if category:
            query = query.filter(
                Q(target_category__isnull=True) | Q(target_category=category)
            )
        
        if product:
            query = query.filter(
                Q(target_product__isnull=True) | Q(target_product=product)
            )
        
        # Order by priority and display order
        query = query.order_by('-priority', 'display_order')
        
        # Apply limit
        if limit:
            query = query[:limit]
        
        return query
    
    @staticmethod
    def get_banner_group(name, banner_type=None, position=None):
        """
        Get a banner group by name or type/position.
        """
        try:
            if name:
                return BannerGroup.objects.get(
                    name=name,
                    status=BannerGroup.Status.ACTIVE
                )
            else:
                return BannerGroup.objects.filter(
                    status=BannerGroup.Status.ACTIVE,
                    banner_type=banner_type,
                    position=position
                ).first()
        except BannerGroup.DoesNotExist:
            return None
    
    @staticmethod
    def record_impression(advertisement, user=None, user_ip=None, device='desktop'):
        """Record advertisement impression."""
        try:
            AdvertisementImpression.objects.create(
                advertisement=advertisement,
                user=user,
                user_ip=user_ip,
                device=device
            )
            advertisement.increment_impression()
        except Exception as e:
            # Silently fail to avoid breaking page rendering
            pass
    
    @staticmethod
    def record_click(advertisement, user=None, user_ip=None):
        """Record advertisement click."""
        try:
            AdvertisementClick.objects.create(
                advertisement=advertisement,
                user=user,
                user_ip=user_ip
            )
        except Exception as e:
            # Silently fail
            pass


@require_http_methods(["POST"])
def record_ad_click(request, ad_id):
    """
    AJAX endpoint to record advertisement clicks.
    """
    try:
        ad = get_object_or_404(Advertisement, id=ad_id)
        user_ip = get_client_ip(request)
        user = request.user if request.user.is_authenticated else None
        
        AdvertisementService.record_click(ad, user=user, user_ip=user_ip)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def record_ad_impression(request, ad_id):
    """
    AJAX endpoint to record advertisement impressions.
    """
    try:
        ad = get_object_or_404(Advertisement, id=ad_id)
        user_ip = get_client_ip(request)
        user = request.user if request.user.is_authenticated else None
        device = request.POST.get('device', 'desktop')
        
        AdvertisementService.record_impression(ad, user=user, user_ip=user_ip, device=device)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Import django models here to avoid circular imports
from django.db import models
