from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.marketing.models import Advertisement, Banner
from .permissions import staff_required


@staff_required
def advertisement_list(request):
    ads = Advertisement.objects.all().order_by('order', '-created_at')
    banners = Banner.objects.all().order_by('order')
    return render(request, 'adminpanel/ads/ad_list.html', {
        'ads': ads,
        'banners': banners,
    })


@staff_required
def advertisement_create(request):
    if request.method == 'POST':
        ad = Advertisement(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            link_url=request.POST.get('link_url', ''),
            ad_type=request.POST.get('ad_type', 'CARD'),
            placement=request.POST.get('placement', 'GLOBAL'),
            bg_color=request.POST.get('bg_color', '#0ea5e9'),
            text_color=request.POST.get('text_color', '#ffffff'),
            order=int(request.POST.get('order', 0)),
            is_active=request.POST.get('is_active') == 'on',
        )
        if request.FILES.get('image'):
            ad.image = request.FILES['image']
        ad.save()
        messages.success(request, f'Reklama "{ad.title}" yaratildi.')
        return redirect('adminpanel:ad_list')
    return render(request, 'adminpanel/ads/ad_form.html', {'ad': None})


@staff_required
def advertisement_edit(request, ad_id):
    ad = get_object_or_404(Advertisement, id=ad_id)
    if request.method == 'POST':
        ad.title = request.POST.get('title')
        ad.description = request.POST.get('description', '')
        ad.link_url = request.POST.get('link_url', '')
        ad.ad_type = request.POST.get('ad_type', ad.ad_type)
        ad.placement = request.POST.get('placement', ad.placement)
        ad.bg_color = request.POST.get('bg_color', ad.bg_color)
        ad.text_color = request.POST.get('text_color', ad.text_color)
        ad.order = int(request.POST.get('order', ad.order))
        ad.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('image'):
            ad.image = request.FILES['image']
        ad.save()
        messages.success(request, 'Reklama yangilandi.')
        return redirect('adminpanel:ad_list')
    return render(request, 'adminpanel/ads/ad_form.html', {'ad': ad})


@require_POST
@staff_required
def advertisement_toggle(request, ad_id):
    ad = get_object_or_404(Advertisement, id=ad_id)
    ad.is_active = not ad.is_active
    ad.save()
    return redirect('adminpanel:ad_list')


@require_POST
@staff_required
def advertisement_delete(request, ad_id):
    ad = get_object_or_404(Advertisement, id=ad_id)
    ad.delete()
    messages.info(request, 'Reklama o\'chirildi.')
    return redirect('adminpanel:ad_list')


@staff_required
def banner_create(request):
    if request.method == 'POST':
        banner = Banner(
            title=request.POST.get('title'),
            subtitle=request.POST.get('subtitle', ''),
            link_url=request.POST.get('link_url', ''),
            banner_type=request.POST.get('banner_type', 'SLIDER'),
            order=int(request.POST.get('order', 0)),
            is_active=request.POST.get('is_active') == 'on',
        )
        if request.FILES.get('image'):
            banner.image = request.FILES['image']
        banner.save()
        messages.success(request, 'Banner qo\'shildi.')
        return redirect('adminpanel:ad_list')
    return render(request, 'adminpanel/ads/banner_form.html')