import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\acer\Desktop\platforma (2) (2)\platforma (2)\platforma')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.telegram_services.models import TelegramSettings, TelegramProduct, TelegramProductCategory
from apps.telegram_services.views import OrderCheckoutView, create_order_view, ProductDetailView

User = get_user_model()

def main():
    print("=== STARTING TELEGRAM GIFTS FLOW VERIFICATION ===")
    
    # 1. Fetch settings
    settings = TelegramSettings.get_settings()
    print(f"Loaded Settings Instance:")
    print(f"  Telegram Username: {settings.gifts_telegram_username}")
    print(f"  Redirect Enabled: {settings.gifts_redirect_enabled}")
    print(f"  Message Template length: {len(settings.gifts_message_template)} chars")
    
    # Ensure there's a Gift product
    category, _ = TelegramProductCategory.objects.get_or_create(
        name='gifts',
        defaults={'display_name': 'Telegram Gifts', 'icon': '🎁'}
    )
    product, _ = TelegramProduct.objects.get_or_create(
        sku='test_gift_product',
        defaults={
            'category': category,
            'name': 'Mystery Gift Box',
            'price_uzs': 150000.00,
            'status': 'active',
            'stock': 100
        }
    )
    print(f"Gift Product in DB: {product.name} (SKU: {product.sku})")
    
    # 2. Test context data on Detail View
    factory = RequestFactory()
    user, _ = User.objects.get_or_create(username='test_gifts_user')
    request = factory.get(f'/telegram-services/products/{product.pk}/')
    request.user = user
    
    view = ProductDetailView()
    view.request = request
    view.object = product
    context = view.get_context_data()
    
    print("\nVerifying Detail View Context parameters:")
    print(f"  gifts_telegram_username: {context.get('gifts_telegram_username')}")
    print(f"  telegram_gift_url: {context.get('telegram_gift_url')}")
    assert context.get('gifts_telegram_username') == "@slx15" or context.get('gifts_telegram_username') == settings.gifts_telegram_username
    assert "https://t.me/" in context.get('telegram_gift_url')
    
    # 3. Test checkout dispatch block
    request_checkout = factory.get(f'/telegram-services/checkout/{product.pk}/')
    request_checkout.user = user
    
    # Add messages mock support
    class DummyStorage:
        def __init__(self, request):
            self.messages = []
        def add(self, level, message, extra_tags=''):
            self.messages.append(message)
        def __iter__(self):
            return iter(self.messages)
            
    request_checkout._messages = DummyStorage(request_checkout)
    
    view_checkout = OrderCheckoutView()
    view_checkout.request = request_checkout
    view_checkout.kwargs = {'product_id': product.pk}
    
    response = view_checkout.dispatch(request_checkout, product_id=product.pk)
    print("\nVerifying Checkout Block:")
    print(f"  Response Status Code: {response.status_code}")
    print(f"  Redirect URL: {response.url}")
    assert response.status_code == 302
    assert str(product.pk) in response.url
    print("  -> Correctly blocked checkout and redirected user back to details!")
    
    # 4. Test direct create order API block
    request_api = factory.post(f'/telegram-services/orders/create/{product.pk}/', content_type='application/json')
    request_api.user = user
    response_api = create_order_view(request_api, product_id=product.pk)
    
    print("\nVerifying Direct Order Creation Block:")
    print(f"  Response Status Code: {response_api.status_code}")
    import json
    data = json.loads(response_api.content)
    print(f"  Response Content: {data}")
    assert response_api.status_code == 400
    assert data['success'] is False
    assert "avtomatik checkout" in data['message']
    print("  -> Correctly rejected API order creation request!")
    
    print("\n=== GIFTS FLOW VERIFICATION COMPLETED SUCCESSFULLY ===")

if __name__ == '__main__':
    main()
