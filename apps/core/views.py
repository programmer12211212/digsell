from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Q, Count, Sum
from decimal import Decimal

from apps.orders.models import Order
from apps.users.models import User, Wallet, WalletTransaction
from apps.videos.models import Video, CourseCategory, VideoPurchase
from apps.marketing.models import Banner


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Video.objects.filter(is_active=True)

        context['banners'] = Banner.objects.filter(is_active=True).order_by('order')[:5]
        context['popular_products'] = products.order_by('-sales_count')[:8]
        context['popular_videos'] = products.filter(product_type='VIDEO').order_by('-views_count')[:6]
        context['discounted_products'] = products.filter(discount_price__isnull=False).order_by('-created_at')[:8]
        context['new_products'] = products.order_by('-created_at')[:8]
        context['recommended_products'] = products.filter(avg_rating__gte=4).order_by('-avg_rating')[:8]
        context['top_rated_videos'] = products.filter(product_type='VIDEO', avg_rating__gte=4).order_by('-avg_rating')[:6]
        context['course_categories'] = CourseCategory.objects.filter(parent__isnull=True)[:12]

        context['stats_data'] = [
            ("Foydalanuvchilar", f"{User.objects.count():,}+", "Kunu-tun faol"),
            ("Mahsulotlar", f"{Video.objects.count():,}+", "Sifatli tanlov"),
            ("Sotuvlar", f"{Order.objects.filter(status='PAID').count():,}+", "Muvaffaqiyatli"),
            ("Daromad", f"{Order.objects.filter(status='PAID').aggregate(s=Sum('final_amount'))['s'] or 0:,.0f}", "Umumiy aylanma"),
        ]

        context['top_sellers'] = User.objects.filter(role='SELLER').annotate(
            total_sales=Sum('seller_videos__sales_count')
        ).order_by('-total_sales')[:6]

        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        wallet, _ = Wallet.objects.get_or_create(user=user)
        context['wallet'] = wallet
        context['my_products_count'] = Video.objects.filter(seller=user).count()
        context['my_purchases_count'] = VideoPurchase.objects.filter(user=user).count()
        context['recent_transactions'] = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:5]
        context['recent_orders'] = Order.objects.filter(buyer=user).order_by('-created_at')[:5]
        context['referral_count'] = User.objects.filter(referred_by=user).count()
        
        # New products to show on dashboard (recently added)
        context['new_products'] = Video.objects.filter(is_active=True).order_by('-created_at')[:8]
        # Site info block (rendered on dashboard instead of balance chart)
        context['site_info'] = (
            "<h4 class='font-bold mb-2'>Platforma haqida</h4>"
            "<p>Bizning platformamiz sifatli video kurslar, raqamli mahsulotlar va xizmatlarni taklif etadi. "
            "Yangi kurslar muntazam qo'shiladi, mualliflarimiz sifatli kontent yaratishga intiladi.</p>"
            "<p class='mt-2'>Qo'shimcha savollar uchun <a href='/support/' class='text-primary-500 underline'>Yordam</a> bo'limiga murojaat qiling.</p>"
        )

        return context


class PurchasesListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "core/purchases.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).order_by('-created_at')


@login_required
def profile_view(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)
    context = {
        'user_obj': user,
        'wallet': wallet,
        'purchases_count': VideoPurchase.objects.filter(user=user).count(),
        'sales_count': Video.objects.filter(seller=user).aggregate(s=Sum('sales_count'))['s'] or 0,
        'referral_count': User.objects.filter(referred_by=user).count(),
    }
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        user.save()
        messages.success(request, "Profil yangilandi.")
        return redirect('core:profile')
    return render(request, 'core/profile.html', context)


@login_required
def referrals_view(request):
    user = request.user
    referrals = User.objects.filter(referred_by=user).order_by('-date_joined')
    referral_link = request.build_absolute_uri(f'/auth/register/?ref={user.referral_code}')
    context = {
        'referrals': referrals,
        'referral_link': referral_link,
        'referral_code': user.referral_code,
        'total_referrals': referrals.count(),
        'bonus_earned': WalletTransaction.objects.filter(
            wallet__user=user, reason__icontains='referral'
        ).aggregate(s=Sum('amount'))['s'] or 0,
    }
    return render(request, 'core/referrals.html', context)


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'core/order_tracking.html', {'order': order})


@login_required
def download_purchase(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user, status__in=['PAID', 'COMPLETED', 'DELIVERED'])
    product = order.product
    if not product:
        raise Http404("Mahsulot topilmadi.")
    return download_digital_product(request, product.id)


@login_required
def download_digital_product(request, product_id):
    product = get_object_or_404(Video, id=product_id)
    has_purchased = VideoPurchase.objects.filter(user=request.user, product=product).exists()
    if not has_purchased and product.seller != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Siz ushbu mahsulotni sotib olmagansiz.")

    digital_file = product.files.filter(is_main=True).first()
    if not digital_file:
        raise Http404("Yuklab olish uchun fayl mavjud emas.")

    try:
        response = FileResponse(digital_file.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{digital_file.file.name.split("/")[-1]}"'
        return response
    except Exception:
        raise Http404("Faylni yuklashda xatolik yuz berdi.")


@login_required
def wallet_history(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'core/wallet_history.html', {'transactions': transactions, 'wallet': wallet})
