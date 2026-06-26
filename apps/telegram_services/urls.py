from django.urls import path
from . import views

app_name = 'telegram_services'

urlpatterns = [
    # Public Pages
    path('', views.TelegramServicesHomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Orders
    path('checkout/<uuid:product_id>/', views.OrderCheckoutView.as_view(), name='checkout'),
    path('orders/create/<uuid:product_id>/', views.create_order_view, name='create_order'),
    path('orders/<uuid:order_id>/payment/', views.OrderPaymentView.as_view(), name='payment'),
    path('orders/<uuid:order_id>/confirm-payment/', views.confirm_payment_view, name='confirm_payment'),
    path('orders/<uuid:order_id>/pay-from-balance/', views.pay_from_balance_view, name='pay_from_balance'),
    path('orders/<uuid:order_id>/create-hamyon-payment/', views.create_hamyon_payment, name='create_hamyon_payment'),
    path('orders/<uuid:order_id>/cancel-hamyon-payment/', views.cancel_hamyon_payment_view, name='cancel_hamyon_payment'),
    path('orders/<uuid:order_id>/check-hamyon-status/', views.check_hamyon_payment_status, name='check_hamyon_status'),
    path('orders/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('my-orders/', views.MyOrdersView.as_view(), name='my_orders'),
    path('rewards/', views.RewardTrackView.as_view(), name='reward_track'),
    path('rewards/claim/<uuid:stage_id>/', views.claim_reward_stage_view, name='reward_claim'),
    
    # API Endpoints
    path('api/user-info/', views.get_user_info_api, name='api_user_info'),
    path('api/products/', views.get_products_api, name='api_products'),
    path('api/my-orders/', views.get_my_orders_api, name='api_my_orders'),
]
