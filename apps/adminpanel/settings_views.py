from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.conf import settings as django_settings

from apps.ai_system.models import AIConfig
from .utils import log_admin_action
from .permissions import staff_required


@staff_required
def settings_center(request):
    ai_config = AIConfig.objects.first()
    return render(request, 'adminpanel/settings/center.html', {
        'ai_config': ai_config,
        'debug': django_settings.DEBUG,
        'site_name': 'Digsell.uz',
    })


@staff_required
def save_settings(request):
    if request.method == 'POST':
        log_admin_action(request.user, 'update_settings', 'Settings', 'global', {
            'site_name': request.POST.get('site_name', 'Digsell.uz'),
        })
        messages.success(request, 'Sozlamalar saqlandi.')
    return redirect('adminpanel:settings')