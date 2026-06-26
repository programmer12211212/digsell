from django.utils import timezone
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST

from apps.videos.models import Video, CourseCategory, VideoPurchase, VideoReview
from apps.orders.models import Order, OrderItem, Cart, CartItem, Coupon
from apps.users.models import Wallet, WalletTransaction
from apps.payments.models import CompanyCard
from apps.payments.wallet_services import WalletPurchaseService
from apps.marketing.models import Promocode, BonusRule


class ProductListView(ListView):
    model = Video
    template_name = "marketplace/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = Video.objects.published().select_related('seller', 'category')
        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        product_type = self.request.GET.get('type')
        sort = self.request.GET.get('sort', 'newest')

        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if cat:
            queryset = queryset.filter(category__slug=cat)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if product_type:
            queryset = queryset.filter(product_type=product_type)

        sort_map = {
            'price_asc': 'price',
            'price_desc': '-price',
            'popular': '-sales_count',
            'rating': '-avg_rating',
            'newest': '-created_at',
        }
        return queryset.order_by(sort_map.get(sort, '-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CourseCategory.objects.filter(parent__isnull=True)
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context


def product_detail(request, slug):
    product = get_object_or_404(Video.objects.published(), slug=slug)
    product.views_count += 1
    product.save(update_fields=['views_count'])

    is_purchased = False
    in_wishlist = False
    user_review = None
    if request.user.is_authenticated:
        is_purchased = VideoPurchase.objects.filter(user=request.user, product=product).exists()
        from apps.marketplace.models import VideoWishlist
        in_wishlist = VideoWishlist.objects.filter(user=request.user, video=product).exists()
        user_review = VideoReview.objects.filter(user=request.user, product=product).first()

    reviews = product.reviews.select_related('user').order_by('-created_at')[:20]

    related = Video.objects.published().filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    return render(request, "marketplace/product_detail.html", {
        "product": product,
        "is_purchased": is_purchased,
        "in_wishlist": in_wishlist,
        "related_products": related,
        "reviews": reviews,
        "user_review": user_review,
    })


@login_required
@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Video.objects.published(), id=product_id)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()
    if not comment:
        messages.error(request, 'Izoh yozing.')
        return redirect('marketplace:product_detail', slug=product.slug)

    review, created = VideoReview.objects.update_or_create(
        user=request.user, product=product,
        defaults={'rating': min(5, max(1, rating)), 'comment': comment},
    )
    avg = product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    product.avg_rating = round(avg, 2)
    product.save(update_fields=['avg_rating'])
    messages.success(request, 'Sharhingiz qabul qilindi!' if created else 'Sharh yangilandi.')
    return redirect('marketplace:product_detail', slug=product.slug)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_view(request):
    cart = _get_or_create_cart(request.user)
    items = cart.items.filter(saved_for_later=False).select_related('product')
    saved_items = cart.items.filter(saved_for_later=True).select_related('product')
    return render(request, 'marketplace/cart.html', {
        'cart': cart,
        'items': items,
        'saved_items': saved_items,
    })


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Video.objects.published(), id=product_id)
    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, saved_for_later=False)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.title}" savatga qo\'shildi.')
    next_url = request.POST.get('next', 'marketplace:cart')
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('marketplace:cart')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Mahsulot savatdan olib tashlandi.")
    return redirect('marketplace:cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect('marketplace:cart')


@login_required
@require_POST
def save_for_later(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.saved_for_later = True
    item.save()
    messages.success(request, "Mahsulot keyinroq uchun saqlandi.")
    return redirect('marketplace:cart')


@login_required
def create_order(request, product_id):
    product = get_object_or_404(Video.objects.published(), id=product_id)
    price = product.discount_price or product.price
    commission = (price * Decimal('0.10')).quantize(Decimal('0.01'))

    order = Order.objects.create(
        buyer=request.user,
        total_amount=price,
        final_amount=price,
        commission_amount=commission,
        status=Order.Status.NEW,
    )
    OrderItem.objects.create(order=order, product=product, price_at_purchase=price)
    return redirect('marketplace:payment_page', order_id=order.id)


@login_required
def checkout_cart(request):
    cart = _get_or_create_cart(request.user)
    items = cart.items.filter(saved_for_later=False)
    if not items.exists():
        messages.warning(request, "Savatingiz bo'sh.")
        return redirect('marketplace:cart')

    total = cart.total
    commission = (total * Decimal('0.10')).quantize(Decimal('0.01'))
    order = Order.objects.create(
        buyer=request.user,
        total_amount=total,
        final_amount=total,
        commission_amount=commission,
        status=Order.Status.NEW,
    )
    for item in items:
        price = item.product.discount_price or item.product.price
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_at_purchase=price,
        )
    items.delete()
    return redirect('marketplace:payment_page', order_id=order.id)


@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    company_cards = CompanyCard.objects.filter(is_active=True)

    if order.status in (Order.Status.PAID, Order.Status.COMPLETED, Order.Status.DELIVERED):
        messages.info(request, "Bu buyurtma allaqachon to'langan.")
        return redirect('core:order_tracking', order_id=order.id)

    if request.method == 'POST':
        wants_json = (
            'application/json' in request.headers.get('Accept', '')
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )

        if 'pay_from_balance' in request.POST:
            result = WalletPurchaseService.purchase_marketplace_order(
                request.user,
                order,
                _complete_order,
            )
            if wants_json:
                if result.get('success'):
                    from django.urls import reverse
                    result['redirect_url'] = reverse('core:order_tracking', kwargs={'order_id': order.id})
                status_code = 200 if result.get('success') else 402
                return JsonResponse(result, status=status_code)

            if result.get('success'):
                messages.success(request, "To'lov muvaffaqiyatli amalga oshirildi!")
                return redirect('core:order_tracking', order_id=order.id)

            messages.error(request, result.get('message', "Balans yetarli emas."))
            return redirect('marketplace:payment_page', order_id=order.id)

        elif request.FILES.get('receipt_image'):
            order.receipt_image = request.FILES['receipt_image']
            order.payment_method = request.POST.get('payment_method', 'BANK_TRANSFER')
            order.status = Order.Status.PENDING
            order.save()
            from apps.notifications.models import Notification
            from apps.users.models import User
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin,
                    notif_type=Notification.Type.ORDER_NEW,
                    title=f"Yangi to'lov cheki: #{order.id}",
                    message=f"{request.user.username} chek yukladi — {order.final_amount} UZS",
                    target_url=f'/admin-console/orders/{order.id}/',
                )
            messages.success(request, "Chek yuborildi. Admin tasdiqlashini kuting.")
            return redirect('core:order_tracking', order_id=order.id)

    return render(request, "marketplace/payment_page.html", {
        "order": order,
        "wallet": wallet,
        "company_cards": company_cards,
    })


def _complete_order(order, user):
    """
    To'liq buyurtma yakunlash logikasi:
    1. Statusni yangilash
    2. Xarid tarixini yaratish
    3. Sotuvchiga pul o'tkazish (Komissiya chegirilgan holda)
    4. Bonus va Referral tizimini ishlatish
    """
    from apps.videos.models import VideoPurchase
    import logging
    logger = logging.getLogger(__name__)

    # Idempotency check: Don't process paid orders twice
    if order.status in (Order.Status.PAID, Order.Status.COMPLETED):
        if VideoPurchase.objects.filter(user=user, order_id=str(order.id)).exists():
            logger.info(f"Order {order.id} already processed. Skipping.")
            return
    try:
        from django.db import transaction
        from apps.users.models import Wallet
        from apps.videos.models import VideoPurchase
        
        with transaction.atomic():
            # Refresh order from DB to avoid race conditions and ensure latest status
            order = Order.objects.select_for_update().get(pk=order.pk)
            
            logger.info(f"Processing completion for Order {order.id}. Total: {order.total_amount}, Final: {order.final_amount}")
            
            # 1. Update order status if not already paid
            if order.status not in (Order.Status.PAID, Order.Status.COMPLETED):
                Order.objects.filter(pk=order.pk).update(status=Order.Status.PAID, updated_at=timezone.now())
                order.status = Order.Status.PAID # Update local instance for loop
                logger.info(f"Order {order.id} status updated to PAID.")

            # 2. Process Items
            items = order.items.all()
            if not items.exists():
                logger.warning(f"Order {order.id} has NO items! Is this a bug in order creation?")

            for item in items:
                product = item.product
                logger.info(f"Processing Item: {product.title} (Seller: {product.seller.username if product.seller else 'NONE'})")
                
                # a. Create Purchase record (idempotent)
                purchase, created = VideoPurchase.objects.get_or_create(
                    user=user, 
                    product=product,
                    defaults={
                        'order_id': str(order.id), 
                        'amount': item.price_at_purchase,
                        'payment_status': VideoPurchase.PaymentStatus.PAID
                    }
                )
                if created:
                    logger.info(f"Created purchase record for user {user.username}, product {product.id}")
                else:
                    logger.info(f"Purchase record already exists for user {user.username}, product {product.id}")
                
                # b. Update Product Stats
                product.sales_count += item.quantity
                product.save(update_fields=['sales_count'])

                # c. Pay Seller
                if product.seller:
                    total_item_price = item.price_at_purchase * item.quantity
                    
                    # Calculate commission for this item
                    if order.total_amount > 0:
                        # Proportion of total order commission
                        comm_proportion = (total_item_price / order.total_amount) * (order.commission_amount or 0)
                    else:
                        # Default 10% if total_amount is zero
                        comm_proportion = total_item_price * Decimal('0.10')
                    
                    seller_amount = (total_item_price - comm_proportion).quantize(Decimal('0.01'))
                    
                    if seller_amount > 0:
                        seller_wallet, _ = Wallet.objects.get_or_create(user=product.seller)
                        
                        logger.info(f"Attempting to pay {seller_amount} UZS to seller {product.seller.username}. Reason: Order {order.id}")
                        
                        try:
                            # Use add_funds which is already atomic internally (nested atomic is fine in Django)
                            success = seller_wallet.add_funds(
                                amount=seller_amount, 
                                reason=f"Sotuv: {product.title} (Buyurtma #{order.id})"
                            )
                            if success is False:
                                logger.error(f"Wallet add_funds returned False for seller {product.seller.id}!")
                            else:
                                logger.info(f"SUCCESS: Payout completed for seller {product.seller.username}. New balance: {seller_wallet.balance}")
                        except Exception as p_err:
                            logger.error(f"FAILED to update seller wallet: {str(p_err)}")
                            raise # Re-raise to rollback transaction
                    else:
                        logger.warning(f"Skipping zero/negative payout ({seller_amount}) for product {product.id}")
                else:
                    logger.warning(f"Product {product.id} has NO seller! Platform keeps 100%?")

            # 3. Bonuses (only apply if this is the first execution)
            # We use created boolean from first purchase or a separate check
            _apply_purchase_bonus(user, order.final_amount)
            _apply_referral_bonus(user, order.final_amount)
            
            logger.info(f"Order {order.id} completion finished successfully.")

    except Exception as e:
        logger.error(f"CRITICAL ERROR in _complete_order for Order {order.id}: {str(e)}", exc_info=True)
        raise


def _apply_purchase_bonus(user, amount):
    """Xarid uchun bonus ballarini hisoblash va qo'shish."""
    rule = BonusRule.objects.filter(is_active=True).first()
    if not rule:
        return
        
    bonus = (amount * rule.percentage / Decimal('100')).quantize(Decimal('0.01'))
    if bonus <= 0:
        return
        
    wallet, _ = Wallet.objects.get_or_create(user=user)
    # Yangi add_bonus_funds metodidan foydalanish (atomar va xavfsiz)
    wallet.add_bonus_funds(amount=bonus, reason='Xarid bonusi (Ball)')


def _apply_referral_bonus(user, amount):
    """Referral (taklif qiluvchi) uchun bonus hisoblash."""
    if not user.referred_by:
        return
        
    bonus = (amount * Decimal('0.05')).quantize(Decimal('0.01'))
    if bonus <= 0:
        return
        
    ref_wallet, _ = Wallet.objects.get_or_create(user=user.referred_by)
    # Referral bonus balansga tushadi
    ref_wallet.add_funds(amount=bonus, reason=f'Referral bonus: {user.username} xaridi uchun')


@login_required
@require_POST
def apply_coupon(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    code = request.POST.get('coupon_code', '').strip().upper()

    promo = Promocode.objects.filter(code__iexact=code, is_active=True).first()
    if not promo:
        coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
        if not coupon:
            return JsonResponse({'success': False, 'message': 'Promo kod topilmadi.'})
        if coupon.discount_percent:
            discount = order.total_amount * coupon.discount_percent / 100
        else:
            discount = coupon.discount_amount
    else:
        if promo.discount_percent:
            discount = order.total_amount * promo.discount_percent / 100
        else:
            discount = promo.discount_amount or Decimal('0')

    order.discount_amount = discount
    order.final_amount = max(order.total_amount - discount, Decimal('0'))
    order.coupon_code = code
    order.save()
    return JsonResponse({
        'success': True,
        'message': f'Promo kod qo\'llandi! Chegirma: {discount:,.0f} so\'m',
        'discount': str(discount),
        'final_amount': str(order.final_amount),
    })


@login_required
def wishlist_view(request):
    from apps.marketplace.models import VideoWishlist
    wishlisted = VideoWishlist.objects.filter(user=request.user).select_related('video', 'video__seller')
    return render(request, 'marketplace/wishlist.html', {'wishlisted': wishlisted})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    from apps.marketplace.models import VideoWishlist
    product = get_object_or_404(Video.objects.published(), id=product_id)
    wishlist, created = VideoWishlist.objects.get_or_create(user=request.user, video=product)
    if not created:
        wishlist.delete()
        return JsonResponse({'success': True, 'added': False, 'message': 'Sevimlilardan olib tashlandi.'})
    return JsonResponse({'success': True, 'added': True, 'message': 'Sevimlilarga qo\'shildi.'})
