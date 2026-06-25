import os
import django
import random
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.utils.text import slugify
from apps.users.models import User, Wallet
from apps.videos.models import Video, CourseCategory
from apps.marketing.models import BonusRule, SpinWheelPrize, Competition, Banner
from apps.payments.models import CompanyCard


def seed():
    print("Seeding Digsell.uz Enterprise Database...")

    v_cats = [
        ("Elektronika", "fas fa-microchip"),
        ("Dasturlash", "fas fa-code"),
        ("Dizayn", "fas fa-paint-brush"),
        ("Marketing", "fas fa-bullhorn"),
        ("Biznes", "fas fa-briefcase"),
        ("Transport", "fas fa-car"),
    ]
    for name, icon in v_cats:
        CourseCategory.objects.get_or_create(name=name, defaults={'slug': slugify(name), 'icon': icon})

    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@Digsell.uz', 'role': 'ADMIN', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin.set_password('admin12345')
        admin.save()
        print("Admin: admin / admin12345")

    sellers = []
    for i in range(1, 6):
        user, created = User.objects.get_or_create(
            username=f'seller{i}',
            email=f'seller{i}@Digsell.uz',
            defaults={'role': 'SELLER', 'is_verified': True}
        )
        if created:
            user.set_password('seller777')
            user.save()
        Wallet.objects.get_or_create(user=user, defaults={'balance': Decimal('500000.00')})
        sellers.append(user)

    demo, created = User.objects.get_or_create(
        username='demo',
        defaults={'email': 'demo@Digsell.uz', 'role': 'USER'}
    )
    if created:
        demo.set_password('demo12345')
        demo.save()
        Wallet.objects.get_or_create(user=demo, defaults={'balance': Decimal('1000000.00')})

    product_data = [
        ("Python Backend asoslari", "Dasturlash", 250000, "VIDEO"),
        ("UI/UX Dizayn 2026", "Dizayn", 180000, "VIDEO"),
        ("E-commerce React Template", "Dasturlash", 450000, "DIGITAL"),
        ("Logo Bundle (100+)", "Dizayn", 120000, "DIGITAL"),
        ("Fitness App Flutter", "Dasturlash", 600000, "DIGITAL"),
        ("iPhone 15 Pro Max", "Elektronika", 15000000, "PHYSICAL"),
        ("MacBook Pro M3", "Elektronika", 25000000, "PHYSICAL"),
        ("SMM Kursi Pro", "Marketing", 350000, "VIDEO"),
        ("Biznes Rejasi Shablon", "Biznes", 80000, "DIGITAL"),
    ]

    for title, cat_name, price, p_type in product_data:
        cat = CourseCategory.objects.get(name=cat_name)
        Video.objects.get_or_create(
            slug=slugify(title),
            defaults={
                'title': title,
                'category': cat,
                'seller': random.choice(sellers),
                'price': Decimal(price),
                'product_type': p_type,
                'description': f"Bu {title} haqida batafsil ma'lumot. Digsell.uz platformasida sifatli mahsulot.",
                'is_active': True,
                'avg_rating': Decimal(str(round(random.uniform(4.0, 5.0), 2))),
                'sales_count': random.randint(5, 100),
                'views_count': random.randint(50, 500),
            }
        )

    BonusRule.objects.get_or_create(
        name='Standart xarid bonusi',
        defaults={'percentage': Decimal('5.00'), 'is_active': True}
    )

    prizes = [
        ('500 bonus', 'BONUS', 500, 30),
        ('1000 bonus', 'BONUS', 1000, 20),
        ('Cashback 2000', 'CASHBACK', 2000, 15),
        ('Yana urinib ko\'ring', 'NONE', 0, 35),
    ]
    for name, ptype, value, prob in prizes:
        SpinWheelPrize.objects.get_or_create(name=name, defaults={
            'prize_type': ptype, 'value': Decimal(value), 'probability': prob
        })

    now = timezone.now()
    Competition.objects.get_or_create(
        title='Haftalik Top Xaridorlar',
        defaults={
            'description': 'Eng ko\'p xarid qilgan foydalanuvchilar uchun sovrinlar',
            'comp_type': 'TOP_BUYER',
            'start_date': now,
            'end_date': now + timedelta(days=7),
            'is_active': True,
        }
    )

    CompanyCard.objects.get_or_create(
        card_number='8600 1234 5678 9012',
        defaults={'card_name': 'Uzcard', 'card_holder': 'Digsell.uz MCHJ', 'is_active': True}
    )
    CompanyCard.objects.get_or_create(
        card_number='9860 9876 5432 1098',
        defaults={'card_name': 'Humo', 'card_holder': 'Digsell.uz MCHJ', 'is_active': True}
    )

    print("Success: Digsell.uz seeding completed!")


if __name__ == "__main__":
    seed()
