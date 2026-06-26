import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from decimal import Decimal
import random
import base64


class Command(BaseCommand):
    help = 'Seed marketplace with real products and categories. Uses Django ORM and is idempotent.'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from django.conf import settings
        from apps.marketplace.models import Category, Product, ProductFile

        User = get_user_model()
        seller = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not seller:
            self.stdout.write(self.style.ERROR('No users found to assign as seller. Create a user first.'))
            return

        categories = [
            {
                'name': 'Telegram Services',
                'slug': 'telegram-services',
                'icon': 'message-circle',
                'description': 'Telegram service integrations and premium Telegram resource categories.',
                'display_order': 1,
                'is_active': True,
                'product_type': 'SERVICE',
                'tags': ['telegram', 'services'],
                'product_titles': [],
            },
            {
                'name': 'Website Source Codes',
                'slug': 'website-source-codes',
                'icon': 'code',
                'description': 'Ready-made website source code packages for ecommerce, marketplaces, CMS, and more.',
                'display_order': 2,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['website', 'source-code'],
                'product_titles': [
                    'Django Ecommerce',
                    'Laravel Ecommerce',
                    'Restaurant POS',
                    'Hotel Management',
                    'Inventory System',
                    'School Management',
                    'CRM System',
                    'Blog CMS',
                    'Portfolio Website',
                    'Landing Page',
                    'Marketplace System',
                    'Invoice System',
                    'Hospital Management',
                    'Gym Management',
                    'Job Portal',
                    'Online Store',
                    'Digital Marketplace',
                    'Auction Website',
                    'Booking System',
                    'Learning Management System',
                ],
            },
            {
                'name': 'Telegram Bot Scripts',
                'slug': 'telegram-bot-scripts',
                'icon': 'bot',
                'description': 'Telegram bot scripts for shops, payments, automation, and chat management.',
                'display_order': 3,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['telegram', 'bot', 'script'],
                'product_titles': [
                    'Telegram Shop Bot',
                    'Telegram Premium Seller',
                    'Telegram Stars Seller',
                    'Telegram Wallet Bot',
                    'Telegram Referral Bot',
                    'Telegram Membership Bot',
                    'Telegram Mini App',
                    'Telegram Channel Manager',
                    'Telegram Payment Bot',
                    'Telegram Giveaway Bot',
                    'Telegram Admin Bot',
                    'Telegram AI Bot',
                    'Telegram Music Bot',
                    'Telegram Download Bot',
                    'Telegram Crypto Bot',
                    'Telegram Marketplace Bot',
                    'Telegram Store Bot',
                    'Telegram Support Bot',
                    'Telegram Invoice Bot',
                    'Telegram Auto Reply Bot',
                ],
            },
            {
                'name': 'Python Scripts',
                'slug': 'python-scripts',
                'icon': 'terminal',
                'description': 'Python automation and utility scripts for data, scraping, AI, and system tasks.',
                'display_order': 4,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['python', 'script'],
                'product_titles': [
                    'Instagram Automation',
                    'TikTok Automation',
                    'Discord Bot',
                    'ChatGPT Assistant',
                    'Web Scraper',
                    'API Parser',
                    'Automation Toolkit',
                    'File Manager',
                    'Backup Tool',
                    'SEO Analyzer',
                    'AI Image Generator',
                    'AI Chat Bot',
                    'PDF Generator',
                    'Email Sender',
                    'YouTube Downloader',
                    'Video Converter',
                    'OCR Tool',
                    'Data Extractor',
                    'Proxy Checker',
                    'Task Scheduler',
                ],
            },
            {
                'name': 'PHP Scripts',
                'slug': 'php-scripts',
                'icon': 'server',
                'description': 'Professional PHP script packages for administration, commerce, billing, and portals.',
                'display_order': 5,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['php', 'script'],
                'product_titles': [
                    'Admin Panel',
                    'CRM',
                    'CMS',
                    'Invoice Generator',
                    'Support System',
                    'Ticket System',
                    'Payment Gateway',
                    'Authentication System',
                    'Affiliate System',
                    'Multi Vendor Shop',
                    'Forum',
                    'Blog',
                    'ERP',
                    'POS',
                    'Hotel Booking',
                    'Appointment System',
                    'Warehouse System',
                    'Payroll',
                    'School Portal',
                    'HR System',
                ],
            },
            {
                'name': 'React Projects',
                'slug': 'react-projects',
                'icon': 'react',
                'description': 'React applications and frontend projects for modern web experiences.',
                'display_order': 6,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['react', 'frontend'],
                'product_titles': [
                    'React Ecommerce',
                    'React Dashboard',
                    'React Portfolio',
                    'React Landing Page',
                    'React CRM',
                    'React Blog Platform',
                    'React SaaS UI',
                    'React Marketplace',
                    'React Admin Panel',
                    'React Social App',
                    'React Chat App',
                    'React Booking App',
                    'React Learning Platform',
                    'React Project Management',
                    'React Finance App',
                    'React Resume Builder',
                    'React News Portal',
                    'React Photo Gallery',
                    'React Analytics Dashboard',
                    'React Media Player',
                ],
            },
            {
                'name': 'HTML Templates',
                'slug': 'html-templates',
                'icon': 'layout',
                'description': 'HTML templates for landing pages, business sites, portfolios, and web presentations.',
                'display_order': 7,
                'is_active': True,
                'product_type': 'SOFTWARE',
                'tags': ['html', 'template'],
                'product_titles': [
                    'Corporate Landing Page',
                    'Startup Landing Page',
                    'Portfolio Template',
                    'Agency Template',
                    'Event Landing Page',
                    'Product Launch Page',
                    'Conference Template',
                    'Service Showcase',
                    'Mobile App Landing Page',
                    'Business Card Website',
                    'Consulting Agency Page',
                    'Fitness Studio Template',
                    'Restaurant Landing Page',
                    'Travel Agency Template',
                    'Education Landing Page',
                    'Digital Agency Template',
                    'Software Product Page',
                    'SaaS Landing Template',
                    'Photography Portfolio',
                    'Personal Resume Page',
                ],
            },
            {
                'name': 'Books',
                'slug': 'books',
                'icon': 'book-open',
                'description': 'Digital books for developers, marketers, business owners, and startup founders.',
                'display_order': 8,
                'is_active': True,
                'product_type': 'EBOOK',
                'tags': ['book', 'ebook'],
                'product_titles': [
                    'Python Mastery',
                    'Django Guide',
                    'Laravel Guide',
                    'PHP Handbook',
                    'JavaScript Handbook',
                    'React Guide',
                    'Business Growth',
                    'Startup Guide',
                    'SEO Guide',
                    'Digital Marketing',
                    'Telegram Marketing',
                    'AI Handbook',
                    'Prompt Engineering',
                    'Cyber Security',
                    'Networking',
                    'Linux Guide',
                    'Docker Guide',
                    'Git Guide',
                    'API Development',
                    'Database Design',
                ],
            },
            {
                'name': 'PDF Resources',
                'slug': 'pdf-resources',
                'icon': 'file-text',
                'description': 'PDF resources, cheat sheets and guides for developers, designers, and marketers.',
                'display_order': 9,
                'is_active': True,
                'product_type': 'DIGITAL',
                'tags': ['pdf', 'guide'],
                'product_titles': [
                    'Python Notes',
                    'Django Notes',
                    'Laravel Notes',
                    'SEO Checklist',
                    'Marketing Checklist',
                    'Telegram API Guide',
                    'Prompt Collection',
                    'AI Cheat Sheets',
                    'Database Cheat Sheet',
                    'JavaScript Notes',
                    'Linux Commands',
                    'Git Commands',
                    'Docker Notes',
                    'Business Templates',
                    'Finance Templates',
                    'Freelance Guide',
                    'Branding Guide',
                    'UX Guide',
                    'UI Guide',
                    'Productivity Guide',
                ],
            },
            {
                'name': 'PPTX Templates',
                'slug': 'pptx-templates',
                'icon': 'file-chart',
                'description': 'Presentation templates for startups, sales, education, finance, and analytics reports.',
                'display_order': 10,
                'is_active': True,
                'product_type': 'DIGITAL',
                'tags': ['pptx', 'presentation'],
                'product_titles': [
                    'Startup Pitch Deck',
                    'Business Presentation',
                    'Marketing Slides',
                    'Sales Deck',
                    'Company Profile',
                    'Investment Pitch',
                    'Education Slides',
                    'Portfolio',
                    'Proposal',
                    'Financial Report',
                    'Project Timeline',
                    'Roadmap',
                    'Analytics Report',
                    'Business Plan',
                    'Technology Presentation',
                ],
            },
            {
                'name': 'Design Resources',
                'slug': 'design-resources',
                'icon': 'palette',
                'description': 'Design asset packs, kits, and UI resources for web, mobile, and branding projects.',
                'display_order': 11,
                'is_active': True,
                'product_type': 'DIGITAL',
                'tags': ['design', 'ui'],
                'product_titles': [
                    'Admin UI Kit',
                    'Dashboard UI',
                    'Figma Mobile Kit',
                    'Landing UI',
                    'Icon Pack',
                    'Illustration Pack',
                    'Glass UI Kit',
                    'Dark UI Kit',
                    'Social Media Kit',
                    'Brand Kit',
                    'Wireframe Kit',
                    'Ecommerce UI',
                    'Portfolio UI',
                    'Mobile Components',
                    'Dashboard Components',
                ],
            },
            {
                'name': 'AI Resources',
                'slug': 'ai-resources',
                'icon': 'brain',
                'description': 'AI resource packs and prompt libraries for productivity, design, marketing, and development.',
                'display_order': 12,
                'is_active': True,
                'product_type': 'DIGITAL',
                'tags': ['ai', 'prompt'],
                'product_titles': [
                    'Prompt Bundle',
                    'ChatGPT Prompts',
                    'Midjourney Prompts',
                    'Cursor Prompts',
                    'Copilot Prompts',
                    'Claude Prompts',
                    'Gemini Prompts',
                    'AI Automation Pack',
                    'AI Business Pack',
                    'AI Marketing Pack',
                    'AI Coding Pack',
                    'AI Productivity Pack',
                    'AI Design Pack',
                    'AI Writing Pack',
                    'AI Research Pack',
                ],
            },
            {
                'name': 'Business Resources',
                'slug': 'business-resources',
                'icon': 'briefcase',
                'description': 'Business and finance resource templates for startups, contracts, invoices, and legal documents.',
                'display_order': 13,
                'is_active': True,
                'product_type': 'DIGITAL',
                'tags': ['business', 'template'],
                'product_titles': [
                    'Invoice Template',
                    'Contract Template',
                    'Resume Template',
                    'CV Template',
                    'Proposal Template',
                    'Business Plan',
                    'Invoice PDF',
                    'Price List',
                    'Quotation Template',
                    'Presentation Kit',
                    'Startup Documents',
                    'HR Documents',
                    'Legal Templates',
                    'Finance Templates',
                    'Marketing Templates',
                ],
            },
            {
                'name': 'Automation Scripts',
                'slug': 'automation-scripts',
                'icon': 'refresh-cw',
                'description': 'Automation scripts for backups, uploads, invoicing, OCR, and business workflow automation.',
                'display_order': 14,
                'is_active': True,
                'product_type': 'SOURCE_CODE',
                'tags': ['automation', 'script'],
                'product_titles': [
                    'Auto Backup',
                    'Auto Email',
                    'Auto Invoice',
                    'Auto Report',
                    'Auto Screenshot',
                    'Auto OCR',
                    'Auto Upload',
                    'Auto Download',
                    'Auto Sync',
                    'Auto Rename',
                    'Auto Compression',
                    'Auto Image Resize',
                    'Auto Telegram Sender',
                    'Auto WhatsApp Sender',
                    'Auto Database Backup',
                    'Auto FTP Upload',
                    'Auto Scheduler',
                    'Auto PDF Merge',
                    'Auto Excel Report',
                    'Auto API Monitor',
                ],
            },
        ]

        image_b64 = (
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
        )
        image_bytes = base64.b64decode(image_b64)
        gallery_root = os.path.join(settings.MEDIA_ROOT, 'products', 'gallery')
        os.makedirs(gallery_root, exist_ok=True)

        self.stdout.write(self.style.NOTICE('Seeding marketplace categories and products...'))

        categories_by_slug = {}
        for category_data in categories:
            category, created = Category.objects.update_or_create(
                slug=category_data['slug'],
                defaults={
                    'name': category_data['name'],
                    'icon': category_data['icon'],
                    'description': category_data['description'],
                    'display_order': category_data['display_order'],
                    'is_active': category_data['is_active'],
                }
            )
            categories_by_slug[category.slug] = category

        created_products = 0
        updated_products = 0

        for category_data in categories:
            category = categories_by_slug[category_data['slug']]
            for title in category_data['product_titles']:
                slug = slugify(title)
                price = Decimal(random.randint(25000, 260000))
                discount = Decimal(random.randint(5, 25))
                sale_price = (price * (Decimal(100) - discount) / Decimal(100)).quantize(Decimal('0.01'))
                old_price = price
                current_price = sale_price
                seo_title = f"{title} - Digsell.uz Digital Marketplace"
                seo_description = f"Buy {title} with instant access and full documentation on Digsell.uz. High-quality digital product for {category.name}."
                short_description = f"{title} is a ready-made {category.name.lower()} product for fast deployment."
                tags = [slugify(category.name)] + category_data['tags']
                tags.append(slugify(title))
                language = 'Python' if 'Python' in title or 'Django' in title or 'Flask' in title else 'PHP' if 'PHP' in title or 'Laravel' in title else 'JavaScript'
                framework = 'Django' if 'Django' in title or 'Python' in category.name else 'Laravel' if 'Laravel' in title else 'React' if 'React' in title else 'Bootstrap'
                file_size = f"{random.randint(2, 45)}MB"
                gallery_files = []
                for index in range(1, 4):
                    gallery_filename = f"{slug}-gallery-{index}.png"
                    gallery_path = os.path.join(gallery_root, gallery_filename)
                    if not os.path.exists(gallery_path):
                        with open(gallery_path, 'wb') as gallery_file:
                            gallery_file.write(image_bytes)
                    gallery_files.append(f"products/gallery/{gallery_filename}")

                product_values = {
                    'seller': seller,
                    'category': category,
                    'title': title,
                    'description': f"{title} is a fully prepared {category.name.lower()} product. Includes source files, setup instructions, and support documentation.",
                    'short_description': short_description,
                    'product_type': category_data['product_type'],
                    'price': old_price,
                    'old_price': old_price,
                    'sale_price': current_price,
                    'tags': ','.join(tags),
                    'is_active': True,
                    'is_verified': True,
                    'featured': random.choice([True, False, False]),
                    'popular': random.choice([True, True, False]),
                    'downloads': random.randint(20, 1500),
                    'rating': Decimal(str(round(random.uniform(4.0, 5.0), 2))),
                    'sales_count': random.randint(10, 1200),
                    'view_count': random.randint(150, 12000),
                    'seo_title': seo_title,
                    'seo_description': seo_description,
                    'short_description': short_description,
                    'language': language,
                    'framework': framework,
                    'file_size': file_size,
                    'gallery': gallery_files,
                }

                product, created = Product.objects.update_or_create(
                    slug=slug,
                    defaults=product_values,
                )

                if created:
                    created_products += 1
                else:
                    updated_products += 1

                if not product.preview_image:
                    preview_name = f"{slug}-preview.png"
                    product.preview_image.save(preview_name, ContentFile(image_bytes), save=True)
                if not product.cover_image:
                    cover_name = f"{slug}-cover.png"
                    product.cover_image.save(cover_name, ContentFile(image_bytes), save=True)

                if not ProductFile.objects.filter(product=product, version='1.0.0').exists():
                    ProductFile.objects.create(
                        product=product,
                        file=ContentFile(b"Digsell marketplace product download file.", name=f"{slug}.zip"),
                        version='1.0.0',
                        changelog=f"Seeded {title} product file.",
                    )

        self.stdout.write(self.style.SUCCESS(
            f'Marketplace seeding complete: {created_products} new products, {updated_products} updated products.'
        ))
