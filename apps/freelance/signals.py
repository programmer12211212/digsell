from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg

from apps.freelance.models import FreelanceReview, FreelancerProfile
from apps.freelance.services.chat import update_top_rated_status


@receiver(post_save, sender=FreelanceReview)
def update_freelancer_rating(sender, instance, **kwargs):
    avg = FreelanceReview.objects.filter(
        freelancer=instance.freelancer
    ).aggregate(avg=Avg("rating"))["avg"]
    if avg is not None:
        instance.freelancer.rating = round(avg, 2)
        instance.freelancer.save(update_fields=["rating"])
        profile = FreelancerProfile.objects.filter(user=instance.freelancer).first()
        if profile:
            update_top_rated_status(profile)


@receiver(post_save, sender=FreelancerProfile)
def ensure_profile_top_rated(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'is_top_rated' in kwargs.get('update_fields'):
        return
    update_top_rated_status(instance)
