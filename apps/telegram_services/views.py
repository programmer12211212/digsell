from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from urllib.parse import quote

from .models import (
    TelegramProduct, TelegramProductCategory, TelegramOrder, 
    TelegramPaymentCard, TelegramNotification, TelegramRewardStage,
    TelegramRewardClaim
)
from .forms import TelegramOrderForm, ProductFilterForm
from .services import TelegramOrderService, UniqueAmountGenerator, TelegramProviderService, TelegramRewardService
from django.db import transaction
from apps.payments.services import HamyonPaymentService
from apps.payments.models import HamyonPayment

logger = logging.getLogger(__name__)

GIFT_ADMIN_TELEGRAM_USERNAME = 'uzwwn'


def build_gift_admin_contact_payload(request, order, payment=None):
    """Create the Telegram admin-contact payload for successful gift orders only."""
    if not request or not order:
        return {'is_visible': False, 'url': '', 'message': '', 'success_message': '', 'button_label': '💬 Adminga yozish'}

    try:
        category_name = getattr(getattr(order.product, 'category', None), 'name', None)
    except Exception:
        category_name = None

    if category_name != 'gifts':
        return {'is_visible': False, 'url': '', 'message': '', 'success_message': '', 'button_label': '💬 Adminga yozish'}

    if payment is None:
        payment = HamyonPayment.objects.filter(
            user=request.user,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id),
        ).order_by('-created_at').first()

    is_success = False
    if payment and payment.status == HamyonPayment.Status.SUCCESS:
        is_success = True

    if not is_success:
        order_status = str(getattr(order, 'status', '') or '')
        if order_status in {'paid', 'processing', 'completed'}:
            is_success = True

    if not is_success:
        payment_status = getattr(getattr(order, 'payment', None), 'payment_status', None)
        if payment_status == 'confirmed':
            is_success = True

    if not is_success:
        return {'is_visible': False, 'url': '', 'message': '', 'success_message': '', 'button_label': '💬 Adminga yozish'}

    product = getattr(order, 'product', None)
    quantity = getattr(order, 'custom_quantity', None) or 1
    requested_amount = payment.requested_amount if payment and payment.requested_amount is not None else order.unique_amount
    paid_amount = payment.amount if payment else order.unique_amount
    paid_at = payment.paid_at or payment.created_at or getattr(order, 'payment_confirmed_at', None) or timezone.now()
    customer_full_name = request.user.get_full_name() or request.user.username

    order_status_label = {
        'paid': "To'lov muvaffaqiyatli",
        'processing': 'Jarayonda',
        'completed': 'Yakunlangan',
    }.get(str(getattr(order, 'status', '') or ''), "To'lov muvaffaqiyatli")

    message_lines = [
        'Salom.',
        '',
        'Men Digsell.uz orqali Telegram Gift sotib oldim.',
        '',
        '━━━━━━━━━━━━━━━━━━━━━━',
        '',
        '🆔 Buyurtma ID:',
        f'{order.id}',
        '',
        '🔑 Unique ID:',
        f'{order.unique_code}',
        '',
        '🎁 Gift Name:',
        f'{getattr(product, "name", "")}',
        '',
        '🎁 Gift ID:',
        f'{getattr(product, "id", "")}',
        '',
        '🏷 Gift Category:',
        f'{getattr(getattr(product, "category", None), "display_name", "") or getattr(getattr(product, "category", None), "name", "")}',
        '',
        '📦 Gift Quantity:',
        f'{quantity}',
        '',
        '💰 Gift Price:',
        f'{order.base_price} UZS',
        '',
        '💵 Requested Amount:',
        f'{requested_amount} UZS',
        '',
        '💳 Paid Amount:',
        f'{paid_amount} UZS',
        '',
        '💳 Payment ID:',
        f'{getattr(payment, "external_id", "") or getattr(payment, "payment_id", "") or "-"}',
        '',
        '🧾 Transaction ID:',
        f'{getattr(order, "transaction_id", None) or getattr(payment, "external_id", "") or "-"}',
        '',
        '💳 Payment Method:',
        'Hamyon Auto Payment',
        '',
        '📅 Payment Date & Time:',
        f'{paid_at}',
        '',
        '👤 Customer Username:',
        f'{request.user.username}',
        '',
        '👤 Customer Full Name:',
        f'{customer_full_name}',
        '',
        '📱 Telegram Username:',
        f'{order.telegram_username}',
        '',
        '🆔 Telegram User ID:',
        f'{order.telegram_user_id or "-"}',
        '',
        '📦 Order Status:',
        f'{order_status_label}',
        '',
        '📦 Delivery Status:',
        'Admin tomonidan qo\'lda yuborish kutilmoqda',
        '',
        '━━━━━━━━━━━━━━━━━━━━━━',
        '',
        'Iltimos ushbu giftni yuborishingizni so\'rayman.',
        '',
        'Rahmat.',
    ]
    message = '\n'.join(message_lines)
    encoded_message = quote(message, safe='')

    success_message = (
        "✅ To'lov muvaffaqiyatli amalga oshirildi.\n\n"
        "Telegram Gift avtomatik yuborilmaydi.\n"
        "Gift administrator tomonidan qo'lda yuboriladi.\n\n"
        'Pastdagi "Adminga yozish" tugmasini bosib administratorga tayyor xabar yuboring.'
    )

    return {
        'is_visible': True,
        'url': f'https://t.me/{GIFT_ADMIN_TELEGRAM_USERNAME}?text={encoded_message}',
        'message': message,
        'success_message': success_message,
        'button_label': '💬 Adminga yozish',
        'admin_username': f'@{GIFT_ADMIN_TELEGRAM_USERNAME}',
    }


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

class TelegramServicesHomeView(TemplateView):
    """Home page for Telegram Services"""
    template_name = 'telegram_services/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured products
        categories = TelegramProductCategory.objects.all()
        context['categories'] = categories
        
        # Featured products by category
        context['featured_stars'] = TelegramProduct.objects.filter(
            category__name='stars',
            status='active',
            is_featured=True
        )[:3]
        
        context['featured_premium'] = TelegramProduct.objects.filter(
            category__name='premium',
            status='active',
            is_featured=True
        )[:3]
        
        context['featured_gifts'] = TelegramProduct.objects.filter(
            category__name='gifts',
            status='active',
            is_featured=True
        )[:3]
        
        return context


class ProductListView(ListView):
    """List all Telegram products with filtering"""
    model = TelegramProduct
    template_name = 'telegram_services/products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TelegramProduct.objects.filter(status='active')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by rarity
        rarity = self.request.GET.get('rarity')
        if rarity:
            queryset = queryset.filter(rarity=rarity)
            
        # Filter by resale
        resale_only = self.request.GET.get('resale')
        if resale_only == 'true':
            queryset = queryset.filter(is_resale=True)
        elif resale_only == 'false':
            queryset = queryset.filter(is_resale=False)
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Sort
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price_uzs')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price_uzs')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ProductFilterForm(self.request.GET)
        context['categories'] = TelegramProductCategory.objects.all()
        context['rarities'] = ProductFilterForm.RARITY_CHOICES
        return context


class ProductDetailView(DetailView):
    """Product detail page"""
    model = TelegramProduct
    template_name = 'telegram_services/products/detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = TelegramProduct.objects.filter(
            category=self.object.category,
            status='active'
        ).exclude(pk=self.object.pk)[:5]
        
        # Load global settings
        from .models import TelegramSettings
        settings = TelegramSettings.get_settings()
        context['telegram_settings'] = settings
        
        if settings and self.object.category.name == 'gifts':
            dest_username = settings.gifts_telegram_username.lstrip('@')
            template = settings.gifts_message_template
            
            import urllib.parse
            from django.utils import timezone
            
            current_date_str = timezone.now().strftime("%Y-%m-%d %H:%M")
            user_username_val = self.request.user.username if self.request.user.is_authenticated else "mehmon"
            
            try:
                formatted_msg = template.format(
                    username=user_username_val,
                    gift_name=self.object.name,
                    price=f"{self.object.price_uzs:,.0f}",
                    product_id=str(self.object.id),
                    current_date=current_date_str
                )
            except Exception:
                formatted_msg = (
                    f"━━━━━━━━━━━━━━\n"
                    f"🎁 GIFT PURCHASE REQUEST\n"
                    f"━━━━━━━━━━━━━━\n\n"
                    f"👤 User: @{user_username_val}\n"
                    f"🎁 Gift:\n{self.object.name}\n\n"
                    f"💰 Price:\n{self.object.price_uzs:,.0f} UZS\n\n"
                    f"🆔 Product ID:\n#{self.object.id}\n\n"
                    f"📅 Date:\n{current_date_str}\n\n"
                    f"🌐 Source:\nDigsell.uz\n\n"
                    f"━━━━━━━━━━━━━━\n\n"
                    f"Assalomu alaykum.\n\n"
                    f"Men ushbu giftni sotib olmoqchiman.\n"
                    f"Iltimos, xarid jarayonini boshlashga yordam bering.\n\n"
                    f"Rahmat."
                )
                
            encoded_msg = urllib.parse.quote(formatted_msg)
            context['telegram_gift_url'] = f"https://t.me/{dest_username}?text={encoded_msg}"
            context['gifts_telegram_username'] = settings.gifts_telegram_username if settings.gifts_telegram_username.startswith('@') else f"@{settings.gifts_telegram_username}"
            
        return context


# ============================================================================
# ORDER VIEWS
# ============================================================================

class OrderCheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout view for creating order"""
    template_name = 'telegram_services/orders/checkout.html'
    login_url = 'users:login'
    
    def dispatch(self, request, *args, **kwargs):
        product_id = self.kwargs.get('product_id')
        try:
            TelegramProduct.objects.get(pk=product_id, status='active')
        except TelegramProduct.DoesNotExist:
            pass
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        
        try:
            product = TelegramProduct.objects.get(pk=product_id, status='active')
            context['product'] = product
            context['form'] = TelegramOrderForm()
            context['payment_cards'] = TelegramPaymentCard.objects.filter(is_active=True)
            context['checkout_quantity'] = self.request.GET.get('quantity', '')
        except TelegramProduct.DoesNotExist:
            context['error'] = 'Product not found'
        
        return context


@login_required
@require_http_methods(["POST"])
def create_order_view(request, product_id):
    """AJAX endpoint to create order"""
    import json
    import re
    try:
        product = get_object_or_404(TelegramProduct, pk=product_id, status='active')
        
        content_type = (request.content_type or '').split(';')[0]
        if content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON structure'}, status=400)
            telegram_username = data.get('telegram_username', '').strip()
            quantity = data.get('quantity')
        else:
            telegram_username = request.POST.get('telegram_username', '').strip()
            quantity = request.POST.get('quantity')

        if not telegram_username:
            return JsonResponse({'success': False, 'message': 'Username is required'}, status=400)
            
        if not telegram_username.startswith('@'):
            return JsonResponse({'success': False, 'message': 'Username must start with @'}, status=400)
            
        cleaned_username = telegram_username.lstrip('@')
        if not re.match(r'^\w{5,32}$', cleaned_username):
            return JsonResponse({'success': False, 'message': 'Invalid Telegram username'}, status=400)
            
        # Quantity validation if provided (e.g. for custom orders)
        custom_qty_val = None
        if quantity is not None and quantity != '':
            try:
                custom_qty_val = int(quantity)
                if custom_qty_val <= 0:
                    return JsonResponse({'success': False, 'message': 'Stars miqdori 0 dan katta bo\'lishi kerak'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'message': 'Stars miqdori butun son bo\'lishi kerak'}, status=400)
        
        if product.sku == 'custom_stars' and not custom_qty_val:
            return JsonResponse({'success': False, 'message': 'Custom Stars uchun miqdor kiritilishi shart'}, status=400)
            
        form_data = {'telegram_username': cleaned_username}
        form = TelegramOrderForm(form_data)
        
        if form.is_valid():
            order, error = TelegramOrderService.create_order(
                request.user, 
                product, 
                cleaned_username,
                custom_quantity=custom_qty_val
            )
            
            if error:
                return JsonResponse({'success': False, 'message': f'Database insert failed: {error}'}, status=400)
            
            return JsonResponse({
                'success': True,
                'order_id': str(order.id),
                'message': 'Order created successfully',
                'unique_code': order.unique_code,
                'unique_amount': float(order.unique_amount),
                'redirect_url': f'/telegram-services/orders/{order.id}/payment/'
            })
        else:
            errors_list = []
            for field, errors in form.errors.items():
                for err in errors:
                    errors_list.append(err)
            error_message = ", ".join(errors_list) if errors_list else "Invalid form data"
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)
    
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


class OrderPaymentView(LoginRequiredMixin, TemplateView):
    """Payment page for order"""
    template_name = 'telegram_services/orders/payment.html'
    login_url = 'users:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        
        try:
            order = TelegramOrder.objects.get(id=order_id, user=self.request.user)
            context['order'] = order
            context['payment_cards'] = TelegramPaymentCard.objects.filter(is_active=True)
            context['payment_details'] = {
                'unique_code': order.unique_code,
                'unique_amount': float(order.unique_amount),
                'base_amount': float(order.base_price),
            }
            
            # Load global settings & expiration
            import datetime
            from .models import TelegramSettings
            settings = TelegramSettings.objects.first()
            context['telegram_settings'] = settings
            
            timeout = settings.payment_confirmation_timeout if settings else 3600
            expires_at = order.created_at + datetime.timedelta(seconds=timeout)
            context['expires_at_epoch'] = int(expires_at.timestamp())
            
            # Fetch user wallet
            from apps.users.models import Wallet
            wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
            context['user_wallet'] = wallet

            payment = HamyonPayment.objects.filter(
                user=self.request.user,
                purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
                purpose_reference=str(order.id),
            ).order_by('-created_at').first()
            context['gift_admin_contact'] = build_gift_admin_contact_payload(self.request, order, payment)
            context['gift_admin_contact_json'] = json.dumps(context['gift_admin_contact'])
            
        except TelegramOrder.DoesNotExist:
            context['error'] = 'Order not found'
        
        return context


@login_required
@require_http_methods(["POST"])
def confirm_payment_view(request, order_id):
    """Mark order payment as confirmed"""
    try:
        order = get_object_or_404(TelegramOrder, id=order_id, user=request.user)
        
        if order.status != 'waiting_payment':
            return JsonResponse({
                'success': False,
                'message': 'Order is not waiting for payment'
            }, status=400)
        # Manual screenshot confirmation removed. Use Hamyon automated flow.
        return JsonResponse({
            'success': False,
            'message': 'Manual screenshot confirmation is disabled. Please use the automated Hamyon payment flow.'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def pay_from_balance_view(request, order_id):
    """Pay order from user's platform balance"""
    try:
        from apps.users.models import Wallet
        from django.db import transaction
        
        order = get_object_or_404(TelegramOrder, id=order_id, user=request.user)
        
        if order.status != 'waiting_payment':
            return JsonResponse({
                'success': False,
                'message': 'Order is not waiting for payment'
            }, status=400)
            
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        if wallet.balance < order.unique_amount:
            return JsonResponse({
                'success': False,
                'message': f"Balansingizda pul yetarli emas. Kerakli: {order.unique_amount:,.0f} UZS. Balans: {wallet.balance:,.0f} UZS"
            }, status=400)
            
        # Deduct balance and confirm payment atomically
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=wallet.id)
            if wallet.balance < order.unique_amount:
                return JsonResponse({'success': False, 'message': 'Mablag\' yetarli emas'}, status=400)
                
            wallet.balance -= order.unique_amount
            wallet.save()
            
            # Create outflow log
            from apps.users.models import WalletTransaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=order.unique_amount,
                tx_type='OUT',
                reason=f"Telegram buyurtmasi uchun to'lov: {order.unique_code}"
            )
            
            # Update order payment details via confirm_payment (single source of truth)
            confirmed = TelegramOrderService.confirm_payment(
                order,
                admin_user=request.user,
                note="Paid via user wallet balance",
                payment_method='wallet_balance',
            )
            
        if confirmed:
            return JsonResponse({
                'success': True,
                'message': 'To\'lov muvaffaqiyatli amalga oshirildi va buyurtma yetkazishga yuborildi!',
                'redirect_url': f'/telegram-services/orders/{order.id}/'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'To\'lov yechildi, lekin buyurtmani yetkazishda xatolik yuz berdi.'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error paying from balance: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_hamyon_payment(request, order_id):
    """Create or return existing Hamyon payment for the order."""
    try:
        order = get_object_or_404(TelegramOrder, id=order_id, user=request.user)
        if order.status != 'waiting_payment':
            return JsonResponse({'success': False, 'message': 'Order is not waiting for payment'}, status=400)

        # Prevent duplicate Hamyon payments
        with transaction.atomic():
            existing = HamyonPayment.objects.select_for_update().filter(
                user=request.user,
                purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
                purpose_reference=str(order.id)
            ).order_by('-created_at').first()

            service = HamyonPaymentService()

            if existing and existing.status == HamyonPayment.Status.PENDING and not existing.is_expired:
                payment = existing
            else:
                payment = service.create_payment(
                    user=request.user,
                    amount=order.unique_amount,
                    purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
                    purpose_reference=str(order.id),
                    description=f"Telegram order {order.unique_code}",
                )

        # Create or update TelegramPayment record
        from .models import TelegramPayment as TPayment
        TPayment.objects.update_or_create(
            order=order,
            defaults={
                'amount': order.unique_amount,
                'currency': 'UZS',
                'payment_method': 'hamyon',
                'payment_details': {'external_id': payment.external_id, 'card': payment.card}
            }
        )

        from apps.payments.payment_ui import serialize_hamyon_payment_for_create

        return JsonResponse({
            'success': True,
            'payment': serialize_hamyon_payment_for_create(payment),
            # Backward compatibility for older clients
            'payment_id': payment.external_id,
            'payment_pk': payment.id,
            'card': payment.card,
            'expires_at': int(payment.expires_at.timestamp()) if payment.expires_at else None,
            'amount': str(payment.amount),
        })
    except Exception as e:
        logger.exception('Error creating Hamyon payment')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cancel_hamyon_payment_view(request, order_id):
    """Cancel a pending Hamyon payment for the order."""
    try:
        order = get_object_or_404(TelegramOrder, id=order_id, user=request.user)
        payment = HamyonPayment.objects.filter(
            user=request.user,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id)
        ).order_by('-created_at').first()

        if not payment:
            return JsonResponse({'success': False, 'message': 'No Hamyon payment found for this order.'}, status=404)

        if payment.status == HamyonPayment.Status.SUCCESS:
            return JsonResponse({'success': False, 'message': 'This payment has already been successful and cannot be canceled.'}, status=400)

        if payment.status != HamyonPayment.Status.PENDING:
            return JsonResponse({'success': False, 'message': 'Payment cannot be canceled because it is already finalized.'}, status=400)

        payment.status = HamyonPayment.Status.CANCELLED
        payment.external_data = payment.external_data or {}
        payment.external_data['cancelled_by_user'] = True
        payment.external_data['cancelled_at'] = timezone.now().isoformat()
        payment.save(update_fields=['status', 'external_data'])

        return JsonResponse({'success': True, 'message': 'Hamyon payment canceled successfully.'})
    except Exception as e:
        logger.exception('Error canceling Hamyon payment')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def check_hamyon_payment_status(request, order_id):
    """Manually verify the latest Hamyon payment status for the order and process it server-side."""
    try:
        order = get_object_or_404(TelegramOrder, id=order_id, user=request.user)
        payment = HamyonPayment.objects.filter(
            user=request.user,
            purpose=HamyonPayment.Purpose.TELEGRAM_ORDER,
            purpose_reference=str(order.id)
        ).order_by('-created_at').first()

        if not payment:
            return JsonResponse({'success': False, 'message': 'No Hamyon payment found for this order.'}, status=404)

        payment.refresh_from_db()
        service = HamyonPaymentService()
        payment = service.process_payment_status(payment)
        payment.refresh_from_db()
        order.refresh_from_db()

        from apps.payments.payment_ui import build_payment_status_payload

        payload = build_payment_status_payload(payment)
        # Backward compatibility for existing Telegram payment page JS
        payload['status'] = payload.get('payment_status')
        payload['order_status'] = payload.get('delivery_status')
        payload['gift_admin_contact'] = build_gift_admin_contact_payload(request, order, payment)

        if payload.get('ui_status') == 'SUCCESS':
            payload['message'] = 'Payment confirmed.'
        elif payload.get('ui_status') == 'WAITING':
            payload['message'] = 'Payment not received yet.'
        elif payload.get('ui_status') in {'CANCELLED', 'EXPIRED'}:
            payload['message'] = 'Payment was cancelled or expired.'
        elif payload.get('ui_status') == 'FAILED':
            payload['message'] = 'Payment failed.'

        return JsonResponse(payload)
    except Exception as e:
        logger.exception('Error checking Hamyon payment status')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail page"""
    model = TelegramOrder
    template_name = 'telegram_services/orders/detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'
    login_url = 'users:login'
    
    def get_queryset(self):
        return TelegramOrder.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['order_logs'] = order.logs.all()[:10]
        context['notifications'] = order.notifications.all()[:5]
        return context


class MyOrdersView(LoginRequiredMixin, ListView):
    """User's orders list"""
    model = TelegramOrder
    template_name = 'telegram_services/orders/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 20
    login_url = 'users:login'
    
    def get_queryset(self):
        return TelegramOrder.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        user_orders = TelegramOrder.objects.filter(user=self.request.user)
        context['total_spent'] = sum(o.unique_amount for o in user_orders)
        context['completed_orders'] = user_orders.filter(status='completed').count()
        context['pending_orders'] = user_orders.filter(status__in=['waiting_payment', 'waiting_confirmation', 'paid', 'processing']).count()
        
        # Filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            context['orders'] = context['orders'].filter(status=status_filter)
        
        return context


class RewardTrackView(LoginRequiredMixin, TemplateView):
    """Reward Track page for Telegram Stars and Premium loyalty."""
    template_name = 'telegram_services/rewards/track.html'
    login_url = 'users:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = TelegramRewardService.get_active_campaign()
        stats = TelegramRewardService.compute_user_stats(self.request.user)

        context['campaign'] = campaign
        context['stats'] = stats
        context['stages'] = []
        context['campaign_progress'] = 0

        if campaign:
            stage_items = list(campaign.stages.filter(is_active=True).order_by('position'))
            # Use equal spacing for stage markers, and overall campaign progress based on total_spent milestones.
            total_stages = len(stage_items)
            total_spent_targets = [stage.target_value for stage in stage_items if stage.target_type == 'total_spent']
            max_spend_target = max(total_spent_targets) if total_spent_targets else (stage_items[-1].target_value if stage_items else Decimal('1'))
            context['campaign_progress'] = min(int((stats['total_spent'] / max_spend_target) * 100), 100) if max_spend_target else 0

            for index, stage in enumerate(stage_items):
                status = TelegramRewardService.get_user_stage_status(self.request.user, stage, stats)
                position_pct = 0 if total_stages <= 1 else int((index / (total_stages - 1)) * 100)
                context['stages'].append({
                    'id': str(stage.id),
                    'title': stage.title,
                    'description': stage.description,
                    'target_label': stage.target_label,
                    'reward_label': stage.reward_label,
                    'reward_description': stage.reward_description,
                    'reward_type': stage.reward_type,
                    'progress': status['progress'],
                    'unlocked': status['unlocked'],
                    'claimed': status['claimed'],
                    'pending': status['pending'],
                    'denied': status['denied'],
                    'can_claim': status['can_claim'],
                    'claim_id': str(status['claim'].id) if status['claim'] else None,
                    'claim_status': status['claim'].status if status['claim'] else None,
                    'claim_requested_at': status['claim'].requested_at if status['claim'] else None,
                    'position_pct': position_pct,
                })

        if campaign and not any(stage['unlocked'] for stage in context['stages']):
            context['next_stage'] = context['stages'][0] if context['stages'] else None
        else:
            context['next_stage'] = None

        return context


@login_required
@require_http_methods(["POST"])
def claim_reward_stage_view(request, stage_id):
    try:
        import json
        stage = get_object_or_404(TelegramRewardStage, id=stage_id, is_active=True)
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            data = {}

        telegram_username = data.get('telegram_username', '').strip()
        if not telegram_username:
            return JsonResponse({'success': False, 'message': 'Telegram username is required.'}, status=400)

        claim, error = TelegramRewardService.create_reward_claim(request.user, stage, telegram_username=telegram_username)
        if error:
            return JsonResponse({'success': False, 'message': error}, status=400)
        return JsonResponse({
            'success': True,
            'message': 'Sorovingiz yuborildi. Sovrin tekshirilgach sizga beriladi.',
            'status': claim.status,
            'stage_id': str(stage.id),
        })
    except Exception as e:
        logger.error(f"Error creating reward claim: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_user_info_api(request):
    """API endpoint to get Telegram user info"""
    try:
        from .models import TelegramProvider
        
        username = request.query_params.get('username', '').strip()
        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        provider = TelegramProvider.objects.filter(is_active=True).first()
        if not provider:
            username_normalized = username.lstrip('@')
            return Response({
                'id': '000000',
                'username': username_normalized,
                'first_name': username_normalized,
                'last_name': '',
                'photo': f'https://ui-avatars.com/api/?name={username_normalized}&background=0ea5e9&color=fff',
                'note': 'No active provider configured, showing fallback preview.'
            })
        
        service = TelegramProviderService(provider)
        result = service.get_user_info(username)
        
        if result['success']:
            return Response({
                'success': True,
                **result['data']
            })
        else:
            return Response(
                {
                    'success': False,
                    'error': result.get('error', 'User not found')
                },
                status=status.HTTP_200_OK
            )
    
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_products_api(request):
    """API endpoint to get products"""
    try:
        category = request.query_params.get('category')
        search = request.query_params.get('search', '').strip()
        
        queryset = TelegramProduct.objects.filter(status='active')
        
        if category:
            queryset = queryset.filter(category__name=category)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        products = queryset.values(
            'id', 'name', 'description', 'price_uzs', 'price_usd', 
            'icon', 'quantity', 'unit', 'category__name'
        )[:50]
        
        return Response(list(products))
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_orders_api(request):
    """API endpoint to get user's orders"""
    try:
        orders = TelegramOrder.objects.filter(user=request.user).values(
            'id', 'unique_code', 'product__name', 'status', 
            'unique_amount', 'created_at', 'completed_at'
        ).order_by('-created_at')[:20]
        
        return Response(list(orders))
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
