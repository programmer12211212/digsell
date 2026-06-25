import os
import django
import sys
# Ensure project root is on sys.path so `config` module is importable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.marketing.context_processors import advertisements_ctx
from apps.marketing.models import Advertisement

# Ensure at least one Advertisement exists (image is optional)
if not Advertisement.objects.exists():
    Advertisement.objects.create(title='Test Card', ad_type='CARD', placement='GLOBAL', is_active=True, order=1)

# Build a simple request-like object
class Req:
    def __init__(self, path='/'):
        self.path = path
        self.session = {}

req = Req(path='/')
ctx = advertisements_ctx(req)
print('advertisements_ctx output:')
for k, v in ctx.items():
    if isinstance(v, list):
        print(k, [str(x) for x in v])
    else:
        print(k, v)
