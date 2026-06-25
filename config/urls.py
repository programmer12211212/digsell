from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # convenience redirects so `/login/`, `/register/`, `/logout/` work
    path('login/', RedirectView.as_view(url=reverse_lazy('users:login'), permanent=False)),
    path('register/', RedirectView.as_view(url=reverse_lazy('users:register'), permanent=False)),
    path('logout/', RedirectView.as_view(url=reverse_lazy('users:logout'), permanent=False)),
    path('', include('apps.core.urls')),
    
    # Auth
    path('auth/', include('apps.users.urls')),
    path('accounts/', include('allauth.urls')),
    
    path('marketplace/', include('apps.marketplace.urls')),
    path('freelance/', include('apps.freelance.urls')),
    path('ai/', include('apps.ai_system.urls')),
    path('payments/', include('apps.payments.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('chat/', include('apps.chat.urls')),
    path('courses/', include('apps.videos.urls')),
    path('marketing/', include('apps.marketing.urls')),
    path('support/', include('apps.support.urls')),
    path('seller/', include('apps.videos.seller_urls')),
    path('admin-console/', include('apps.adminpanel.urls')),
    path('telegram-services/', include('apps.telegram_services.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
