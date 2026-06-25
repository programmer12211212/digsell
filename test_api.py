#!/usr/bin/env python
import os
import django
import json
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.freelance.models.profile import FreelancerProfile

# Get CSRF token first (or we can get it from the form)
user = User.objects.get(username='farrux_dev')
print(f"Testing API for user: {user.username}")

# Make a request to the profile edit endpoint
session = requests.Session()

# Get the CSRF token
response = session.get('http://127.0.0.1:8000/freelance/dashboard/freelancer/')
print(f"GET response status: {response.status_code}")

# Extract CSRF token from cookies
csrf_token = session.cookies.get('csrftoken')
print(f"CSRF Token: {csrf_token}")

# Now try to make a POST request
test_data = {
    'title': 'Test Title From API',
    'bio': 'Test Bio From API',
    'hourly_rate': 75000,
    'experience_years': 8,
    'availability': 'FULL_TIME',
    'phone': '+998901234567',
    'telegram': 'test_user'
}

headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token or '',
}

response = session.post(
    'http://127.0.0.1:8000/freelance/profile/edit/',
    json=test_data,
    headers=headers
)

print(f"POST response status: {response.status_code}")
print(f"POST response content-type: {response.headers.get('content-type')}")

# Check if we got JSON back
try:
    resp_json = response.json()
    print(f"JSON Response: {resp_json}")
except:
    print(f"Response is NOT JSON - first 100 chars: {response.text[:100]}")

# Check if data was saved
profile = FreelancerProfile.objects.get(user=user)
print(f"\nProfile after API call:")
print(f"Title: {profile.title}")
print(f"Bio: {profile.bio}")
print(f"Hourly Rate: {profile.hourly_rate}")
print(f"Experience: {profile.experience_years}")
print(f"Phone: {profile.phone}")
print(f"Telegram: {profile.telegram}")

