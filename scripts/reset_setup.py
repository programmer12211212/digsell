import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from django.core.management import call_command

def setup():
    print("Creating superusers...")
    try:
        User.objects.create_superuser('uchqunbekc', 'uchqun@digsell.uz', 'uchqunbek0707')
        User.objects.create_superuser('davronc', 'davron@digsell.uz', 'davron0808')
        # Admin is already in seed_data, but let's be safe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@digsell.uz', 'admin12345')
        print("Superusers created.")
    except Exception as e:
        print(f"Superuser creation error (might already exist): {e}")

    print("Initializing Telegram Services...")
    try:
        call_command('init_telegram_services')
        print("Telegram Services initialized.")
    except Exception as e:
        print(f"Telegram Services init error: {e}")

    print("Seeding general data...")
    try:
        # Import seed from script
        from scripts.seed_data import seed
        seed()
        print("General data seeded.")
    except Exception as e:
        print(f"Seed data error: {e}")

if __name__ == "__main__":
    setup()
