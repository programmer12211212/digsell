from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from apps.marketplace.models import Product
from apps.videos.models import Video
from .services import listing_status
from .utils import log_admin_action, broadcast_activity
from .permissions import staff_required


@staff_required
def listing_list(request):
    status = request.GET.get('status', '')
    view_mode = request.GET.get('view', 'table')
    q = request.GET.get('q', '')

    products = Product.objects.select_related('seller', 'category').order_by('-created_at')
    videos = Video.objects.select_related('seller', 'category').order_by('-created_at')

    if q:
        products = products.filter(Q(title__icontains=q) | Q(seller__username__icontains=q))
        videos = videos.filter(Q(title__icontains=q) | Q(seller__username__icontains=q))

    items = []
    for p in products[:100]:
        st = listing_status(product=p)
        if status and st != status:
            continue
        items.append({
            'kind': 'product',
            'obj': p,
            'status': st,
            'title': p.title,
            'seller': p.seller,
            'price': p.price,
            'created_at': p.created_at,
            'image': p.preview_image.url if p.preview_image else None,
        })
    for v in videos[:100]:
        st = listing_status(video=v)
        if status and st != status:
            continue
        items.append({
            'kind': 'video',
            'obj': v,
            'status': st,
            'title': v.title,
            'seller': v.seller,
            'price': v.price,
            'created_at': v.created_at,
            'image': v.thumbnail.url if v.thumbnail else None,
        })
    items.sort(key=lambda x: x['created_at'], reverse=True)

    return render(request, 'adminpanel/listings/list.html', {
        'items': items,
        'status_filter': status,
        'view_mode': view_mode,
        'query': q,
    })


@require_POST
@staff_required
def listing_approve(request, kind, item_id):
    if kind == 'product':
        obj = get_object_or_404(Product, id=item_id)
        obj.is_verified = True
        obj.is_active = True
        obj.save(update_fields=['is_verified', 'is_active'])
    else:
        obj = get_object_or_404(Video, id=item_id)
        obj.is_active = True
        obj.save(update_fields=['is_active'])
    log_admin_action(request.user, 'approve_listing', kind, item_id)
    broadcast_activity({'type': 'activity_item', 'icon': '✅', 'text': f"Tasdiqlandi: {obj.title}"})
    return JsonResponse({'success': True})


@require_POST
@staff_required
def listing_reject(request, kind, item_id):
    if kind == 'product':
        obj = get_object_or_404(Product, id=item_id)
        obj.is_verified = False
        obj.is_active = False
        obj.save(update_fields=['is_verified', 'is_active'])
    else:
        obj = get_object_or_404(Video, id=item_id)
        obj.is_active = False
        obj.save(update_fields=['is_active'])
    log_admin_action(request.user, 'reject_listing', kind, item_id)
    broadcast_activity({'type': 'activity_item', 'icon': '❌', 'text': f"Rad etildi: {obj.title}"})
    return JsonResponse({'success': True})


@require_POST
@staff_required
def listing_bulk_action(request):
    action = request.POST.get('action')
    ids = request.POST.getlist('ids')
    count = 0
    for raw in ids:
        kind, item_id = raw.split(':', 1)
        if kind == 'product':
            obj = Product.objects.filter(id=item_id).first()
            if not obj:
                continue
            if action == 'approve':
                obj.is_verified = True
                obj.is_active = True
                obj.save(update_fields=['is_verified', 'is_active'])
            elif action == 'reject':
                obj.is_verified = False
                obj.is_active = False
                obj.save(update_fields=['is_verified', 'is_active'])
        else:
            obj = Video.objects.filter(id=item_id).first()
            if not obj:
                continue
            obj.is_active = action == 'approve'
            obj.save(update_fields=['is_active'])
        count += 1
        log_admin_action(request.user, f'bulk_{action}_listing', kind, item_id)
    broadcast_activity({'type': 'activity_item', 'icon': '📢', 'text': f'Bulk {action}: {count} ta e\'lon'})
    return JsonResponse({'success': True, 'count': count})