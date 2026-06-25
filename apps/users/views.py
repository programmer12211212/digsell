from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from allauth.socialaccount.models import SocialApp
from .forms import CustomUserCreationForm
from .models import User, Wallet
from .forms import SellerApplicationForm
from .models import SellerApplication
from django.urls import reverse


def _social_app_enabled(request, provider_name: str) -> bool:
    try:
        current_site = get_current_site(request)
    except Exception:
        return False
    return SocialApp.objects.filter(provider=provider_name, sites__id=current_site.id).exists()


def login_view(request):
    google_login_enabled = _social_app_enabled(request, 'google')
    # Support rendering and submission via Django's AuthenticationForm
    from django.contrib.auth.forms import AuthenticationForm

    if request.method == "POST":
        # Accept either 'identifier' or 'username' in the posted form
        identifier = request.POST.get('identifier') or request.POST.get('username') or ''
        password = request.POST.get('password', '')

        # Resolve identifier (email or phone) to actual username if necessary
        username_to_auth = identifier
        if '@' in identifier:
            try:
                u = User.objects.get(email=identifier)
                username_to_auth = u.username
            except User.DoesNotExist:
                username_to_auth = identifier
        elif identifier.startswith('+') or identifier.isdigit():
            try:
                u = User.objects.get(phone=identifier)
                username_to_auth = u.username
            except User.DoesNotExist:
                username_to_auth = identifier

        form = AuthenticationForm(request, data={'username': username_to_auth, 'password': password})
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.username}!")
            return redirect('core:dashboard')
        else:
            messages.error(request, "Login yoki parol noto'g'ri.")
    else:
        form = AuthenticationForm(request)

    return render(request, "users/login.html", {
        "google_login_enabled": google_login_enabled,
        "form": form,
    })


def register_view(request):
    google_login_enabled = _social_app_enabled(request, 'google')
    ref_code = request.GET.get('ref') or request.POST.get('ref_code', '')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Wallet.objects.get_or_create(user=user)

            if ref_code:
                referrer = User.objects.filter(referral_code=ref_code).first()
                if referrer and referrer != user:
                    user.referred_by = referrer
                    user.save(update_fields=['referred_by'])

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz!")
            return redirect('core:dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {
        "form": form,
        "google_login_enabled": google_login_enabled,
        "ref_code": ref_code,
    })


def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz.")
    return redirect('users:login')


@login_required
@require_POST
def toggle_follow(request, user_id):
    return JsonResponse({'success': False, 'message': 'Follow funksiyasi hozircha mavjud emas.'}, status=501)


@login_required
def seller_apply(request):
    """View for users to submit seller application."""
    existing = SellerApplication.objects.filter(user=request.user).order_by('-created_at').first()
    if request.method == 'POST':
        form = SellerApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, 'Sizning arizangiz yuborildi. Admin tasdiqlashini kuting.')
            return redirect('core:dashboard')
    else:
        form = SellerApplicationForm(instance=existing)

    return render(request, 'users/seller_apply.html', {
        'form': form,
        'existing': existing,
    })
