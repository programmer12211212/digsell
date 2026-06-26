from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import base64
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed sample Banner and Advertisement records for development/testing'

    def handle(self, *args, **options):
        from apps.marketing.models import Banner, Advertisement

        # tiny 1x1 PNG placeholder
        png_b64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
        png_bytes = base64.b64decode(png_b64)

        now = timezone.now()

        # Hero banners (SLIDER)
        hero_data = [
            {'title': 'Telegram Stars Boost', 'subtitle': 'Instant Stars delivery for your channel', 'link_url': '/telegram-services/products/?category=stars', 'order': 1},
            {'title': 'Premium Upgrade', 'subtitle': 'Unlock Telegram Premium benefits', 'link_url': '/telegram-services/products/?category=premium', 'order': 2},
            {'title': 'Advanced Bot Scripts', 'subtitle': 'Ready-to-use Telegram Bot source code', 'link_url': '/marketplace/?category=telegram-bots', 'order': 3},
            {'title': 'Python Automation Kits', 'subtitle': 'Scripts to automate your workflows', 'link_url': '/marketplace/?category=python-scripts', 'order': 4},
        ]

        created_banners = 0
        for d in hero_data:
            b, created = Banner.objects.get_or_create(title=d['title'], defaults={
                'subtitle': d['subtitle'],
                'link_url': d['link_url'],
                'banner_type': 'SLIDER',
                'order': d['order'],
                'is_active': True,
                'created_at': now,
            })
            # attach placeholder image if missing
            if not b.image:
                b.image.save(slugify(b.title)+'.png', ContentFile(png_bytes), save=True)
            created_banners += 1

        # Advertisement cards (CARD)
        ads_data = [
            {'title': 'Website Source Codes', 'description': 'Premium website templates and source codes', 'link_url': '/marketplace/?category=website-codes', 'placement': 'MARKETPLACE', 'order': 1},
            {'title': 'Programming eBook', 'description': 'Downloadable programming ebooks (PDF)', 'link_url': '/marketplace/?category=books', 'placement': 'HOME', 'order': 2},
            {'title': 'AI Prompt Packs', 'description': 'Curated ChatGPT prompt collections', 'link_url': '/marketplace/?category=ai-tools', 'placement': 'SIDEBAR', 'order': 3},
            {'title': 'Invoice PDF Template', 'description': 'Professional invoice templates', 'link_url': '/marketplace/?category=pdf-resources', 'placement': 'MARKETPLACE', 'order': 4},
            {'title': 'React Admin Dashboard', 'description': 'Modern admin dashboard templates', 'link_url': '/marketplace/?category=react-projects', 'placement': 'HOME', 'order': 5},
        ]

        created_ads = 0
        for d in ads_data:
            ad, created = Advertisement.objects.get_or_create(title=d['title'], defaults={
                'description': d.get('description',''),
                'link_url': d.get('link_url',''),
                'ad_type': 'CARD',
                'placement': d.get('placement','GLOBAL'),
                'order': d.get('order', 0),
                'is_active': True,
                'show_from': now - timedelta(days=1),
                'show_until': now + timedelta(days=90),
            })
            if not ad.image:
                ad.image.save(slugify(ad.title)+'.png', ContentFile(png_bytes), save=True)
            created_ads += 1

        # Promotion banners (BANNER)
        promo_data = [
            {'title': 'Summer Sale - Up to 50% Off', 'subtitle': 'Limited time discounts on select resources', 'link_url': '/marketplace/?promo=summer', 'order': 1},
            {'title': 'New: Telegram Mini Apps', 'subtitle': 'Launch your Mini App quickly', 'link_url': '/marketplace/?category=telegram-mini-apps', 'order': 2},
            {'title': 'Startup Pitch Decks', 'subtitle': 'Professional pitch decks for startups', 'link_url': '/marketplace/?category=pitch-decks', 'order': 3},
        ]

        created_promos = 0
        for d in promo_data:
            b, created = Banner.objects.get_or_create(title=d['title'], defaults={
                'subtitle': d.get('subtitle',''),
                'link_url': d.get('link_url',''),
                'banner_type': 'WEB',
                'order': d.get('order',0),
                'is_active': True,
                'created_at': now,
            })
            if not b.image:
                b.image.save(slugify(b.title)+'.png', ContentFile(png_bytes), save=True)
            created_promos += 1

        # Sidebar banners
        sidebar_data = [
            {'title': 'Freelance Resources', 'description': 'Resume templates & contracts', 'link_url': '/marketplace/?category=freelance-resources', 'placement': 'SIDEBAR', 'order': 1},
            {'title': 'Design UI Kits', 'description': 'Figma and UI kits', 'link_url': '/marketplace/?category=design-resources', 'placement': 'SIDEBAR', 'order': 2},
        ]
        created_sidebar = 0
        for d in sidebar_data:
            ad, created = Advertisement.objects.get_or_create(title=d['title'], defaults={
                'description': d.get('description',''),
                'link_url': d.get('link_url',''),
                'ad_type': 'CARD',
                'placement': d.get('placement','SIDEBAR'),
                'order': d.get('order',0),
                'is_active': True,
                'show_from': now - timedelta(days=1),
                'show_until': now + timedelta(days=90),
            })
            if not ad.image:
                ad.image.save(slugify(ad.title)+'.png', ContentFile(png_bytes), save=True)
            created_sidebar += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_banners} hero banners, {created_ads} ads, {created_promos} promos, {created_sidebar} sidebar ads'))
