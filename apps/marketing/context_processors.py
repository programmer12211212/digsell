from django.utils import timezone
from .models import Advertisement


def _active_ads(ad_type, placement=None):
    now = timezone.now()
    qs = Advertisement.objects.filter(is_active=True)
    if placement:
        qs = qs.filter(placement__in=[placement, Advertisement.Placement.GLOBAL])
    else:
        qs = qs.filter(ad_type=ad_type)
    ads = []
    for ad in qs.order_by('order'):
        if ad.show_from and now < ad.show_from:
            continue
        if ad.show_until and now > ad.show_until:
            continue
        if ad.ad_type == ad_type:
            ads.append(ad)
    return ads


def advertisements_ctx(request):
    path = request.path
    placement = Advertisement.Placement.GLOBAL
    if path == '/' or path.startswith('/dashboard'):
        placement = Advertisement.Placement.HOME
    elif path.startswith('/marketplace'):
        placement = Advertisement.Placement.MARKETPLACE
    elif path.startswith('/courses'):
        placement = Advertisement.Placement.COURSES

    popup = _active_ads(Advertisement.AdType.POPUP, placement)
    cards = _active_ads(Advertisement.AdType.CARD, Advertisement.Placement.SIDEBAR)
    if not cards:
        cards = _active_ads(Advertisement.AdType.CARD, placement)
    banners = _active_ads(Advertisement.AdType.BANNER, placement)

    dismissed = request.session.get('dismissed_ads', [])
    popup = [p for p in popup if str(p.id) not in dismissed]

    return {
        'ad_cards': cards[:2],
        'ad_popup': popup[0] if popup else None,
        'ad_banners': banners[:3],
    }
