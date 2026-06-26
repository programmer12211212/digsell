import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.contrib.auth import get_user_model

try:
    c = Client()
    User = get_user_model()
    
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        superuser = User.objects.create_superuser(
            username='temp_admin', 
            email='temp@example.com', 
            password='temp_password'
        )
    c.force_login(superuser)
    
    # 1. Fetch admin login (anonymous)
    c.logout()
    print("Testing admin login page...")
    res_login = c.get('/admin/login/')
    assert res_login.status_code == 200
    assert b"admin_custom.css" in res_login.content
    assert b"admin_effects.js" in res_login.content
    print("-> Admin login page contains custom CSS and JS.")
    
    # 2. Login again
    c.force_login(superuser)
    
    # 3. Fetch admin dashboard / index
    print("Testing admin dashboard...")
    res_dashboard = c.get('/admin/')
    assert res_dashboard.status_code == 200
    # Let's verify that the custom css/js is also loaded in Jazzmin admin
    assert b"css/admin_custom.css" in res_dashboard.content or b"admin_custom.css" in res_dashboard.content
    assert b"js/admin_effects.js" in res_dashboard.content or b"admin_effects.js" in res_dashboard.content
    print("-> Admin dashboard contains custom CSS and JS references.")
    
    # 4. Check if the files exist in the static and collected static directories
    static_css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'admin_custom.css')
    static_js_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'admin_effects.js')
    collected_css_path = os.path.join(settings.STATIC_ROOT, 'css', 'admin_custom.css')
    collected_js_path = os.path.join(settings.STATIC_ROOT, 'js', 'admin_effects.js')
    
    assert os.path.exists(static_css_path), "Missing static css!"
    assert os.path.exists(static_js_path), "Missing static js!"
    assert os.path.exists(collected_css_path), "Missing collected css!"
    assert os.path.exists(collected_js_path), "Missing collected js!"
    print("-> Checked static files successfully.")
    
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
    
except Exception as e:
    import traceback
    print("VERIFICATION FAILED:")
    traceback.print_exc()
    sys.exit(1)
