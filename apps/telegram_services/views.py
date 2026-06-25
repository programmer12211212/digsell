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
import logging

from .models import (
    TelegramProduct, TelegramProductCategory, TelegramOrder, 
    TelegramPaymentCard, TelegramNotification
)
from .forms import TelegramOrderForm, ProductFilterForm
from .services import TelegramOrderService, UniqueAmountGenerator, TelegramProviderService

logger = logging.getLogger(__name__)


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
            product = TelegramProduct.objects.get(pk=product_id, status='active')
            if product.category.name == 'gifts':
                from django.contrib import messages
                messages.warning(request, "Gifts mahsulotlarini avtomatik checkout orqali sotib ololmaysiz. Iltimos Telegram orqali bog'laning.")
                return redirect('telegram_services:product_detail', pk=product.pk)
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
        if product.category.name == 'gifts':
            return JsonResponse({'success': False, 'message': 'Gifts mahsulotlarini avtomatik checkout orqali sotib ololmaysiz.'}, status=400)
        
        if request.content_type == 'application/json':
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
            
        # Extract screenshot & note
        if request.FILES.get('payment_screenshot'):
            order.payment_screenshot = request.FILES.get('payment_screenshot')
            
        note = request.POST.get('confirmation_note', '').strip()
        
        # Update order status
        order.status = 'waiting_confirmation'
        order.save()
        
        # Log action
        from .models import TelegramOrderLog
        msg = f'User confirmed payment. Note: {note}' if note else 'User confirmed payment. Awaiting admin verification.'
        TelegramOrderLog.objects.create(
            order=order,
            action='payment_pending',
            status_to='waiting_confirmation',
            message=msg,
            performed_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Payment confirmation submitted. Please wait for admin verification.',
            'redirect_url': f'/telegram-services/orders/{order.id}/'
        })
    
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
            
            # Update order payment details
            order.payment_method = 'wallet_balance'
            order.save()
            
            payment = order.payment
            payment.payment_method = 'wallet_balance'
            payment.save()
            
            # Confirm payment (auto-delivery triggers internally if enabled)
            confirmed = TelegramOrderService.confirm_payment(order, admin_user=request.user, note="Paid via user wallet balance")
            
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


# ============================================================================
# API ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
            return Response(
                {'error': 'No active provider configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        service = TelegramProviderService(provider)
        result = service.get_user_info(username)
        
        if result['success']:
            return Response(result['data'])
        else:
            return Response(
                {'error': result.get('error', 'User not found')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return Response(
            {'error': str(e)},
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
