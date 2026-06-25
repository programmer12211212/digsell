from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.freelance.models import Milestone, FreelancerProfile
from apps.freelance.services.notifications import notify_milestone_due
from apps.freelance.services.ai import ai_recommendations


@shared_task
def check_milestone_deadlines():
    soon = timezone.now() + timedelta(days=2)
    milestones = Milestone.objects.filter(
        due_date__lte=soon,
        due_date__gte=timezone.now(),
        is_completed=False,
    ).select_related("project")
    for m in milestones:
        notify_milestone_due(m)


@shared_task
def send_freelance_email(user_id, subject, body):
    from django.core.mail import send_mail
    from django.conf import settings
    from apps.users.models import User
    user = User.objects.filter(id=user_id).first()
    if user and user.email:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


@shared_task
def send_freelance_sms(user_id, message):
    from apps.users.models import User
    user = User.objects.filter(id=user_id).first()
    if user and user.phone:
        # Provider interface — production da SMS gateway ulanadi
        pass


@shared_task
def compute_ai_recommendations(user_id):
    from apps.users.models import User
    user = User.objects.filter(id=user_id).first()
    if user:
        return ai_recommendations(user)
    return []
