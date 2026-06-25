from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.users.models import User
from .utils import log_admin_action, broadcast_activity
from .permissions import staff_required


@staff_required
def premium_list(request):
    plans = SubscriptionPlan.objects.all()
    subscriptions = UserSubscription.objects.select_related('user', 'plan').order_by('-start_date')
    return render(request, 'adminpanel/premium/list.html', {
        'plans': plans,
        'subscriptions': subscriptions,
        'active_count': subscriptions.filter(is_active=True).count(),
    })


@require_POST
@staff_required
def grant_premium(request, user_id):
    user = get_object_or_404(User, id=user_id)
    plan_id = request.POST.get('plan_id')
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    end_date = timezone.now() + timedelta(days=30)
    sub, _ = UserSubscription.objects.update_or_create(
        user=user,
        defaults={'plan': plan, 'end_date': end_date, 'is_active': True, 'auto_renew': False},
    )
    log_admin_action(request.user, 'grant_premium', 'User', user_id, {'plan': plan.name})
    broadcast_activity({'type': 'activity_item', 'icon': '⭐', 'text': f'Premium berildi: {user.username}'})
    return JsonResponse({'success': True, 'plan': plan.name})