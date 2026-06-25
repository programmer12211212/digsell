from django.urls import path
from . import seller_views

app_name = 'seller'

urlpatterns = [
    path('', seller_views.seller_dashboard, name='dashboard'),
    path('add/', seller_views.product_create, name='product_create'),
    path('edit/<int:product_id>/', seller_views.product_edit, name='product_edit'),
]
