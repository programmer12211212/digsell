import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User

for u in User.objects.all():
    print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | Superuser: {u.is_superuser}")
