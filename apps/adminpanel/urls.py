from django.urls import path
from django.views.generic import RedirectView

from . import views, api
from . import (
    user_views, order_views, marketplace_views, report_views,
    analytics_views, security_views, monitoring_views,
    advertisement_views, support_views,
    listing_views, payment_views, premium_views,
    freelance_views,
    notification_views, settings_views, admin_views, log_views,
)

app_name = 'adminpanel'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='adminpanel:dashboard', permanent=False)),
    path('dashboard/', views.admin_enterprise_dashboard, name='dashboard'),

    # Modules
    path('orders/', order_views.order_list_admin, name='order_list'),
    path('orders/<uuid:order_id>/', order_views.order_detail_admin, name='order_detail'),
    path('orders/<uuid:order_id>/status/', order_views.update_order_status, name='update_order_status'),
    path('orders/bulk/', order_views.order_bulk_action, name='order_bulk'),

    path('listings/', listing_views.listing_list, name='listings'),
    path('listings/<str:kind>/<int:item_id>/approve/', listing_views.listing_approve, name='listing_approve'),
    path('listings/<str:kind>/<int:item_id>/reject/', listing_views.listing_reject, name='listing_reject'),
    path('listings/bulk/', listing_views.listing_bulk_action, name='listing_bulk'),

    path('users/', user_views.user_list_view, name='user_list'),
    path('users/<int:user_id>/toggle/', user_views.toggle_user_status, name='toggle_user'),
    path('users/<int:user_id>/balance/', user_views.adjust_balance, name='adjust_balance'),
    path('users/<int:user_id>/verify/', user_views.verify_seller, name='verify_seller'),
    path('users/<int:user_id>/premium/', premium_views.grant_premium, name='grant_premium'),

    path('payments/', payment_views.payment_dashboard, name='payments'),
    path('payments/<int:withdrawal_id>/approve/', payment_views.approve_withdrawal, name='approve_withdrawal'),
    path('payments/<int:withdrawal_id>/reject/', payment_views.reject_withdrawal, name='reject_withdrawal'),

    path('freelance/', freelance_views.freelance_dashboard, name='freelance_dashboard'),
    path('freelance/freelancers/', freelance_views.freelancer_list, name='freelance_freelancers'),
    path('freelance/freelancers/<int:profile_id>/verify/', freelance_views.verify_freelancer, name='verify_freelancer'),
    path('freelance/escrow/<int:tx_id>/approve/', freelance_views.approve_escrow, name='approve_escrow'),
    path('freelance/escrow/<int:tx_id>/reject/', freelance_views.reject_escrow, name='reject_escrow'),
    path('freelance/dispute/<int:dispute_id>/resolve/', freelance_views.resolve_dispute, name='resolve_dispute'),
    path('freelance/commission/', freelance_views.save_commission, name='save_commission'),

    path('premium/', premium_views.premium_list, name='premium'),
    path('tickets/', support_views.ticket_list_admin, name='ticket_list'),
    path('tickets/<int:ticket_id>/', support_views.ticket_detail_admin, name='ticket_detail'),
    path('tickets/<int:ticket_id>/reply/', support_views.ticket_reply_admin, name='ticket_reply'),

    path('statistics/', analytics_views.analytics_center, name='statistics'),
    path('analytics/', analytics_views.analytics_center, name='analytics'),
    path('notifications/', notification_views.notification_center, name='notifications'),
    path('settings/', settings_views.settings_center, name='settings'),
    path('settings/save/', settings_views.save_settings, name='settings_save'),
    path('admins/', admin_views.admin_list, name='admins'),
    path('admins/create/', admin_views.admin_create, name='admin_create'),
    path('logs/', log_views.log_center, name='logs'),

    path('security/', security_views.security_center, name='security'),
    path('security/block-ip/', security_views.block_ip, name='block_ip'),
    path('security/unblock/<int:ip_id>/', security_views.unblock_ip, name='unblock_ip'),
    path('monitoring/', monitoring_views.monitoring_center, name='monitoring'),

    path('ads/', advertisement_views.advertisement_list, name='ad_list'),
    path('ads/create/', advertisement_views.advertisement_create, name='ad_create'),
    path('ads/<int:ad_id>/edit/', advertisement_views.advertisement_edit, name='ad_edit'),
    path('ads/<int:ad_id>/toggle/', advertisement_views.advertisement_toggle, name='ad_toggle'),
    path('ads/<int:ad_id>/delete/', advertisement_views.advertisement_delete, name='ad_delete'),
    path('ads/banner/create/', advertisement_views.banner_create, name='banner_create'),

    path('products/', marketplace_views.product_list_admin, name='product_list'),
    path('categories/', marketplace_views.category_list_admin, name='category_list'),
    path('videos/', marketplace_views.video_list_admin, name='video_list'),

    path('export/users/', report_views.export_users_csv, name='export_users'),
    path('export/orders/', report_views.export_orders_csv, name='export_orders'),
    path('export/orders/pdf/', report_views.export_orders_pdf, name='export_orders_pdf'),

    # API
    path('api/dashboard/', api.dashboard_data, name='api_dashboard'),
    path('api/analytics/', api.analytics_data, name='api_analytics'),
    path('api/activity/', api.activity_feed, name='api_activity'),
    path('api/notifications/', api.notifications_data, name='api_notifications'),
    path('api/orders/', api.orders_list, name='api_orders'),
    path('api/notifications/mark/<int:notif_id>/', notification_views.mark_notification_read, name='api_mark_notif'),
    path('api/notifications/mark-all/', notification_views.mark_all_read, name='api_mark_all_notif'),
]
