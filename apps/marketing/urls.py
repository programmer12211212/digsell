from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('bonus/', views.bonus_page, name='bonus_page'),
    path('bonus/claim/', views.claim_daily_bonus, name='claim_daily_bonus'),
    path('spin/', views.spin_wheel, name='spin_wheel'),
    path('competitions/', views.competitions_view, name='competitions'),
    path('ad/<int:ad_id>/dismiss/', views.dismiss_ad, name='dismiss_ad'),
    path('ad/<int:ad_id>/click/', views.track_ad_click, name='track_ad_click'),
]
