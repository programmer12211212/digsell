"""URLs for advertisements app."""
from django.urls import path
from . import views

app_name = 'advertisements'

urlpatterns = [
    path('click/<uuid:ad_id>/', views.record_ad_click, name='record_click'),
    path('impression/<uuid:ad_id>/', views.record_ad_impression, name='record_impression'),
]
