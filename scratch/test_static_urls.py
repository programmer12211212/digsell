import os
import sys
import django
import re

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client

try:
    c = Client()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    superuser = User.objects.filter(is_superuser=True).first()
    c.force_login(superuser)
    
    # Get the admin index page
    print("Fetching /admin/ ...")
    response = c.get('/admin/')
    print("Admin status code:", response.status_code)
    
    content = response.content.decode('utf-8', errors='ignore')
    
    # Find all stylesheet links
    # Matches href="url" in <link rel="stylesheet" ... href="url" ...>
    css_links = re.findall(r'<link[^>]+href=["\']([^"\']+\.css(?:\?[^"\']*)?)["\']', content)
    
    # Find all script src links
    # Matches src="url" in <script ... src="url" ...>
    js_links = re.findall(r'<script[^>]+src=["\']([^"\']+\.js(?:\?[^"\']*)?)["\']', content)
            
    print(f"\nFound {len(css_links)} stylesheets:")
    for link in css_links:
        # Strip query parameters like ?v=123
        clean_link = link.split('?')[0]
        res = c.get(clean_link)
        print(f"CSS: {link} -> Status: {res.status_code}")
        if res.status_code != 200:
            print(f"  [ERROR] Failed to load stylesheet: {clean_link}")
            
    print(f"\nFound {len(js_links)} scripts:")
    for link in js_links:
        # Strip query parameters
        clean_link = link.split('?')[0]
        res = c.get(clean_link)
        print(f"JS: {link} -> Status: {res.status_code}")
        if res.status_code != 200:
            print(f"  [ERROR] Failed to load script: {clean_link}")
            
except Exception as e:
    import traceback
    traceback.print_exc()
