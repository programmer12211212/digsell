#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.freelance.models.profile import FreelancerProfile
from apps.users.models import User

user = User.objects.get(username='farrux_dev')
profile = FreelancerProfile.objects.get(user=user)
print(f"Title: {profile.title}")
print(f"Bio: {profile.bio}")
print(f"Hourly Rate: {profile.hourly_rate}")
print(f"Experience: {profile.experience_years}")
print(f"Phone: {profile.phone}")
print(f"Telegram: {profile.telegram}")
