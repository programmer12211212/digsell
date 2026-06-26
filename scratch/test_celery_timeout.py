import os
import sys
import django
import time

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def run_test():
    start = time.time()
    
    broker_url = getattr(settings, 'CELERY_BROKER_URL', '')
    redis_active = False
    
    if broker_url.startswith('redis://') or broker_url.startswith('rediss://'):
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(broker_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            print(f"Checking Redis connection to {host}:{port}...")
            s = socket.create_connection((host, port), timeout=0.1)
            s.close()
            redis_active = True
            print("Redis is online!")
        except Exception as e:
            print("Redis check failed:", e)
            redis_active = False
    
    if redis_active:
        print("Dispatching Celery task...")
        from apps.payments.tasks import check_single_hamyon_payment
        check_single_hamyon_payment.apply_async(args=[1], countdown=30)
    else:
        print("Redis is offline, skipping Celery task dispatch.")
        
    print(f"Time taken: {time.time() - start:.4f} seconds")

run_test()
