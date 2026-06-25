from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from apps.marketplace.models import Product, Category
from apps.videos.models import Video
from django.contrib import messages
from .permissions import staff_required

@staff_required
def product_list_admin(request):
    products = Product.objects.all().select_related('seller', 'category').order_by('-created_at')
    return render(request, 'adminpanel/marketplace/product_list.html', {'products': products})

@staff_required
def category_list_admin(request):
    categories = Category.objects.all()
    return render(request, 'adminpanel/marketplace/category_list.html', {'categories': categories})

@staff_required
def video_list_admin(request):
    videos = Video.objects.all().select_related('seller', 'category').order_by('-created_at')
    return render(request, 'adminpanel/marketplace/video_list.html', {'videos': videos})