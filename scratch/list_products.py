import os
import sys
import django

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.telegram_services.models import TelegramProduct

for p in TelegramProduct.objects.all():
    print(f"ID: {p.id} | Name: {p.name} | SKU: {p.sku} | Price UZS: {p.price_uzs} | Status: {p.status}")
