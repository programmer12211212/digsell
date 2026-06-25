from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
import random

from .models import DailyBonus, SpinWheelPrize, SpinWheelLog, Competition, Reward, Advertisement
from apps.users.models import Wallet, WalletTransaction
from apps.orders.models import Order
from apps.videos.models import VideoPurchase


@login_required
def claim_daily_bonus(request):
    user = request.user
    today = timezone.now().date()

    if DailyBonus.objects.filter(user=user, claimed_at__date=today).exists():
        messages.warning(request, "Bugun allaqachon bonus olgansiz. Ertaga qaytib keling!")
        return redirect('marketing:bonus_page')

    amount = random.randint(500, 5000)
    DailyBonus.objects.create(user=user, amount=amount)

    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet.bonus_points += int(amount)
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet, amount=amount, tx_type='IN', reason="Kunlik bonus",
    )

    messages.success(request, f"Tabriklaymiz! Sizga {amount:,} bonus berildi.")
    return redirect('marketing:bonus_page')


@login_required
def spin_wheel(request):
    user = request.user
    today = timezone.now().date()

    if SpinWheelLog.objects.filter(user=user, created_at__date=today).exists():
        return render(request, 'marketing/spin_wheel.html', {
            'error': 'Bugungi imkoniyatingizdan foydalanib bo\'lgansiz.',
            'can_spin': False,
        })

    prizes = list(SpinWheelPrize.objects.all())
    if not prizes:
        return render(request, 'marketing/spin_wheel.html', {
            'error': 'Hozircha sovrinlar yo\'q.',
            'can_spin': False,
        })

    if request.method == 'POST':
        prize = random.choices(prizes, weights=[p.probability for p in prizes], k=1)[0]
        SpinWheelLog.objects.create(user=user, prize=prize)

        if prize.prize_type in ('BONUS', 'CASHBACK'):
            wallet, _ = Wallet.objects.get_or_create(user=user)
            if prize.prize_type == 'BONUS':
                wallet.bonus_points += int(prize.value)
            else:
                wallet.cashback_balance += prize.value
            wallet.save()
            WalletTransaction.objects.create(
                wallet=wallet, amount=prize.value, tx_type='IN',
                reason=f"Spin Wheel: {prize.name}",
            )
        return render(request, 'marketing/spin_result.html', {'prize': prize})

    return render(request, 'marketing/spin_wheel.html', {'can_spin': True, 'prizes': prizes})


@login_required
def bonus_page(request):
    user = request.user
    today = timezone.now().date()
    wallet, _ = Wallet.objects.get_or_create(user=user)
    claimed_today = DailyBonus.objects.filter(user=user, claimed_at__date=today).exists()
    spun_today = SpinWheelLog.objects.filter(user=user, created_at__date=today).exists()
    return render(request, 'marketing/bonus_page.html', {
        'wallet': wallet,
        'claimed_today': claimed_today,
        'spun_today': spun_today,
    })


def competitions_view(request):
    now = timezone.now()
    active = Competition.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    top_buyers = top_sellers = top_referrals = []

    if request.user.is_authenticated:
        week_ago = now - timedelta(days=7)
        top_buyers = Order.objects.filter(
            status='PAID', created_at__gte=week_ago
        ).values('buyer__username').annotate(total=Sum('final_amount')).order_by('-total')[:10]

        top_sellers = VideoPurchase.objects.filter(
            purchased_at__gte=week_ago
        ).values('product__seller__username').annotate(count=Count('id')).order_by('-count')[:10]

        from apps.users.models import User
        top_referrals = User.objects.filter(
            referred_by__isnull=False, date_joined__gte=week_ago
        ).values('referred_by__username').annotate(count=Count('id')).order_by('-count')[:10]

    rewards = Reward.objects.select_related('competition').all()[:12]
    return render(request, 'marketing/competitions.html', {
        'competitions': active,
        'top_buyers': top_buyers,
        'top_sellers': top_sellers,
        'top_referrals': top_referrals,
        'rewards': rewards,
    })


@require_POST
def dismiss_ad(request, ad_id):
    dismissed = request.session.get('dismissed_ads', [])
    if str(ad_id) not in dismissed:
        dismissed.append(str(ad_id))
        request.session['dismissed_ads'] = dismissed
    return redirect(request.POST.get('next', '/'))


def track_ad_click(request, ad_id):
    ad = Advertisement.objects.filter(id=ad_id).first()
    if ad:
        ad.click_count += 1
        ad.save(update_fields=['click_count'])
        if ad.link_url:
            return redirect(ad.link_url)
    return redirect('/')
