import os
import django
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.videos.models import CourseCategory
from django.utils.text import slugify

categories = [
    'Python', 'Django', 'Trading', 'Forex', 'Crypto', 
    'Grafik Dizayn', 'Photoshop', 'Mobilografiya', 
    'Marketing', 'SMM', 'Sun’iy Intellekt', 
    'Dasturlash', 'IELTS', 'Ingliz Tili'
]

def seed():
    for name in categories:
        cat, created = CourseCategory.objects.get_or_create(
            name=name,
            defaults={'slug': slugify(name)}
        )
        if created:
            print(f"Created category: {name}")
        else:
            print(f"Category already exists: {name}")

if __name__ == "__main__":
    seed()
