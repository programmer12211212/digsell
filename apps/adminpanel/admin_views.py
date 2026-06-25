from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.users.models import User
from .utils import log_admin_action
from .permissions import staff_required


@staff_required
def admin_list(request):
    admins = User.objects.filter(is_staff=True).order_by('-date_joined')
    return render(request, 'adminpanel/admins/list.html', {'admins': admins})


@require_POST
@staff_required
def admin_create(request):
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    if not username or not password:
        messages.error(request, "Username va parol majburiy.")
        return redirect('adminpanel:admins')
    if User.objects.filter(username=username).exists():
        messages.error(request, "Bu username band.")
        return redirect('adminpanel:admins')
    user = User.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        is_staff=True,
        is_active=True,
        role=User.Role.ADMIN,
    )
    log_admin_action(request.user, 'create_admin', 'User', user.id)
    messages.success(request, f'Admin {username} yaratildi.')
    return redirect('adminpanel:admins')