from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify

from .models import Video, CourseCategory, DigitalFile


def _seller_required(view):
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_seller_approved or request.user.role in ('SELLER', 'ADMIN', 'SUPER_ADMIN') or request.user.is_staff):
            messages.error(request, 'Siz sotuvchi sifatida tasdiqlanmagansiz. Avval sotuvchi bo‘lish uchun murojaat qiling.')
            return redirect('users:seller_apply')
        return view(request, *args, **kwargs)
    return login_required(wrapper)


@login_required
def seller_dashboard(request):
    # If user is not an approved seller, show the apply/need-approval page
    if not (request.user.is_seller_approved or request.user.role in ('SELLER',) or request.user.is_staff):
        return render(request, 'seller/need_approval.html')
    products = Video.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'seller/dashboard.html', {
        'products': products,
        'total_sales': sum(p.sales_count for p in products),
    })


@_seller_required
def product_create(request):
    categories = CourseCategory.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Nom kiritilishi shart.')
            return redirect('seller:product_create')

        slug = slugify(title)
        counter = 1
        base_slug = slug
        while Video.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        cat_id = request.POST.get('category')
        category = CourseCategory.objects.filter(id=cat_id).first() if cat_id else None

        video = Video.objects.create(
            title=title,
            slug=slug,
            description=request.POST.get('description', ''),
            product_type=request.POST.get('product_type', 'DIGITAL'),
            category=category,
            seller=request.user,
            price=request.POST.get('price', 0) or 0,
            discount_price=request.POST.get('discount_price') or None,
            is_active=request.POST.get('is_active') == 'on',
        )
        if request.FILES.get('thumbnail'):
            video.thumbnail = request.FILES['thumbnail']
            video.save()
        if request.FILES.get('preview_video'):
            video.preview_video = request.FILES['preview_video']
            video.save()
        if request.FILES.get('digital_file'):
            DigitalFile.objects.create(product=video, file=request.FILES['digital_file'], is_main=True)

        messages.success(request, f'"{title}" muvaffaqiyatli qo\'shildi!')
        return redirect('seller:dashboard')
    return render(request, 'seller/product_form.html', {'categories': categories, 'product': None})


@_seller_required
def product_edit(request, product_id):
    product = get_object_or_404(Video, id=product_id, seller=request.user)
    categories = CourseCategory.objects.all()
    if request.method == 'POST':
        product.title = request.POST.get('title', product.title)
        product.description = request.POST.get('description', product.description)
        product.product_type = request.POST.get('product_type', product.product_type)
        product.price = request.POST.get('price', product.price) or 0
        dp = request.POST.get('discount_price')
        product.discount_price = dp if dp else None
        product.is_active = request.POST.get('is_active') == 'on'
        cat_id = request.POST.get('category')
        product.category = CourseCategory.objects.filter(id=cat_id).first() if cat_id else None
        if request.FILES.get('thumbnail'):
            product.thumbnail = request.FILES['thumbnail']
        if request.FILES.get('preview_video'):
            product.preview_video = request.FILES['preview_video']
        product.save()
        if request.FILES.get('digital_file'):
            DigitalFile.objects.filter(product=product, is_main=True).delete()
            DigitalFile.objects.create(product=product, file=request.FILES['digital_file'], is_main=True)
        messages.success(request, 'Mahsulot yangilandi.')
        return redirect('seller:dashboard')
    return render(request, 'seller/product_form.html', {'categories': categories, 'product': product})
