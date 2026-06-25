from django.test import Client
from django.contrib.auth import get_user_model
from apps.marketing.models import Advertisement
from apps.videos.models import Video
import uuid
from apps.orders.models import Order

c = Client()
# admin login via POST
r = c.post('/auth/login/', {'identifier':'admin_test','password':'AdminPass123!'})
print('admin login:', r.status_code, getattr(r, 'url', None))
# create ad
ad_data = {'title':'Test Ad','description':'desc','ad_type':'CARD','placement':'GLOBAL','bg_color':'#ff0000','text_color':'#ffffff','order':'1','is_active':'on'}
r = c.post('/admin-console/ads/create/', ad_data, follow=True)
print('create ad status:', r.status_code)
print('ads count:', Advertisement.objects.filter(title='Test Ad').count())

# ensure testuser exists
User = get_user_model()
user = User.objects.filter(username='testuser1').first()
if not user:
    user = User.objects.create_user(username='testuser1', email='test1@example.com', password='TestPass123!')

# create product
slug_base = 'buyme'
unique_slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"
try:
    video = Video.objects.create(title='BuyMe', slug=unique_slug, description='d', product_type='VIDEO', category=None, seller=user, price=100)
    print('video created id:', video.id)
except Exception as e:
    print('video create error', e)
    video = Video.objects.filter(seller=user).first()
    print('using existing video id', getattr(video,'id',None))

# login as user and create order
c.post('/auth/login/', {'identifier':'testuser1','password':'TestPass123!'})
order_resp = c.post(f'/marketplace/buy/{video.id}/')
print('create_order status:', order_resp.status_code, getattr(order_resp, 'url', None))
print('orders count:', Order.objects.count())
