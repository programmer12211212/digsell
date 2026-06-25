import random
import string
import requests
import logging
import os
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import (
    TelegramOrder, TelegramPayment, TelegramProvider, 
    TelegramProviderLog, TelegramOrderLog, TelegramNotification,
    TelegramSettings, TelegramProduct
)

logger = logging.getLogger(__name__)

def log_to_fragmently_file(message: str):
    try:
        log_dir = os.path.join(settings.BASE_DIR, 'storage', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'fragmently.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        logger.error(f"Failed to write to fragmently.log: {str(e)}")


class UniqueAmountGenerator:
    """Generate unique payment amounts"""
    
    @staticmethod
    def generate_unique_code():
        """Generate a unique reference code"""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ensure uniqueness
        while TelegramOrder.objects.filter(unique_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        return code
    
    @staticmethod
    def generate_unique_amount(base_amount: Decimal, min_variance: int = 100, max_variance: int = 999):
        """
        Generate unique amount by adding random variance
        
        Example: 12000 → 12183, 12492, 12731
        """
        variance = random.randint(min_variance, max_variance)
        unique_amount = base_amount + Decimal(variance)
        return unique_amount, variance


class TelegramProviderService:
    """Service for Telegram Provider API Integration"""
    
    def __init__(self, provider: TelegramProvider):
        self.provider = provider
        self.base_url = "https://api.fragmently.uz/api/v1" if provider.name == 'fragmently' else ""
        self.headers = {
            'X-API-Token': provider.api_token or '',
            'Content-Type': 'application/json'
        }
    
    def _log_request(self, method: str, endpoint: str, request_data: dict, response_data: dict = None, status_code: int = None, error: str = ""):
        """Log provider API requests"""
        TelegramProviderLog.objects.create(
            provider=self.provider,
            method=method,
            endpoint=endpoint,
            request_data=request_data or {},
            response_data=response_data or {},
            status_code=status_code,
            error=error
        )
        
        # Log to fragmently.log file
        log_message = (
            f"API Request:\n"
            f"  Method: {method}\n"
            f"  URL: {endpoint}\n"
            f"  Headers: {json.dumps(self.headers, indent=2)}\n"
            f"  Payload: {json.dumps(request_data, indent=2) if request_data else 'None'}\n"
            f"API Response:\n"
            f"  Status Code: {status_code}\n"
            f"  Body: {json.dumps(response_data, indent=2) if response_data else 'None'}\n"
            f"  Error: {error}\n"
            f"--------------------------------------------------"
        )
        log_to_fragmently_file(log_message)
    
    def test_connection(self) -> dict:
        """Test API connection"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if self.provider.is_test:
            res_data = {'success': True, 'message': 'Mock API connection active'}
            self._log_request('GET', f"{self.base_url}/account/balance", {}, res_data, 200)
            return {'success': True, 'data': res_data}
            
        try:
            url = f"{self.base_url}/account/balance"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('GET', url, {}, response_json, response.status_code)
            
            if response.status_code == 200:
                return {'success': True, 'data': response_json}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('GET', f"{self.base_url}/account/balance", {}, None, None, error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_balance(self) -> dict:
        """Get provider account balance"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if self.provider.is_test:
            res_data = {
                'balance': float(self.provider.balance),
                'stars_balance': float(self.provider.stars_balance),
                'premium_balance': float(self.provider.premium_balance)
            }
            self._log_request('GET', f"{self.base_url}/account/balance", {}, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            url = f"{self.base_url}/account/balance"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('GET', url, {}, response_json, response.status_code)
            
            if response.status_code == 200:
                return {'success': True, 'data': response_json}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('GET', f"{self.base_url}/account/balance", {}, None, None, error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_user_info(self, telegram_username: str) -> dict:
        """Get Telegram user info"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if not telegram_username:
            return {'success': False, 'error': 'Username is required'}
            
        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"
        url = f"{self.base_url}/user/info"
        payload = {'username': username}
        
        if self.provider.is_test:
            res_data = {
                'id': '765432109',
                'username': username.lstrip('@'),
                'first_name': 'Sotdim User',
                'last_name': 'Test',
                'photo': f'https://ui-avatars.com/api/?name={username.lstrip("@")}&background=0ea5e9&color=fff'
            }
            self._log_request('POST', url, payload, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('POST', url, payload, response_json, response.status_code)
            
            if response.status_code == 200:
                return {'success': True, 'data': response_json}
            else:
                return {'success': False, 'error': f"User not found or HTTP {response.status_code}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('POST', url, payload, None, None, error_msg)
            return {'success': False, 'error': error_msg}
    
    def send_stars(self, telegram_username: str, quantity: int) -> dict:
        """Send Telegram Stars"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if not telegram_username:
            return {'success': False, 'error': 'Username is required'}
            
        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"
        
        try:
            qty = int(quantity)
            if qty <= 0:
                return {'success': False, 'error': 'Quantity must be greater than 0'}
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Quantity must be integer'}
            
        payload = {
            "query": username,
            "quantity": qty,
            "payment_method": "ton",
            "wallet_version": "V4R2"
        }
        
        url = f"{self.base_url}/buy-stars/"
        
        if self.provider.is_test:
            import uuid
            res_data = {
                'transaction_id': f'txn_stars_{uuid.uuid4().hex[:12]}',
                'status': 'delivered',
                'query': username,
                'quantity': qty
            }
            self._log_request('POST', url, payload, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('POST', url, payload, response_json, response.status_code)
            
            if response.status_code in [200, 201]:
                return {'success': True, 'data': response_json}
            else:
                error_msg = response_json.get('message') or response_json.get('error') or f"HTTP {response.status_code}"
                return {'success': False, 'error': f"Fragmently API rejected request: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('POST', url, payload, None, None, error_msg)
            return {'success': False, 'error': f"Provider unavailable: {error_msg}"}
    
    def send_premium(self, telegram_username: str, months: int) -> dict:
        """Send Telegram Premium subscription"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if not telegram_username:
            return {'success': False, 'error': 'Username is required'}
            
        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"
        
        try:
            qty = int(months)
            if qty <= 0:
                return {'success': False, 'error': 'Quantity must be greater than 0'}
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Quantity must be integer'}
            
        payload = {
            "query": username,
            "mountity": qty,
            "payment_method": "usdt_ton",
            "wallet_version": "V4R2"
        }
        
        url = f"{self.base_url}/buy-premium/"
        
        if self.provider.is_test:
            import uuid
            res_data = {
                'transaction_id': f'txn_prem_{uuid.uuid4().hex[:12]}',
                'status': 'delivered',
                'query': username,
                'quantity': qty
            }
            self._log_request('POST', url, payload, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('POST', url, payload, response_json, response.status_code)
            
            if response.status_code in [200, 201]:
                return {'success': True, 'data': response_json}
            else:
                error_msg = response_json.get('message') or response_json.get('error') or f"HTTP {response.status_code}"
                return {'success': False, 'error': f"Fragmently API rejected request: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('POST', url, payload, None, None, error_msg)
            return {'success': False, 'error': f"Provider unavailable: {error_msg}"}
    
    def send_gift(self, telegram_username: str, gift_id: str) -> dict:
        """Send Telegram Gift"""
        if not self.provider.api_token:
            return {'success': False, 'error': 'API token missing'}
            
        if not telegram_username:
            return {'success': False, 'error': 'Username is required'}
            
        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"
        url = f"{self.base_url}/buy-gift/"
        payload = {
            "query": username,
            "gift_id": gift_id,
            "payment_method": self.provider.payment_method or "ton",
            "wallet_version": "V4R2"
        }
        
        if self.provider.is_test:
            import uuid
            res_data = {
                'transaction_id': f'txn_gift_{uuid.uuid4().hex[:12]}',
                'status': 'delivered',
                'query': username,
                'gift_id': gift_id
            }
            self._log_request('POST', url, payload, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": response.text}
                
            self._log_request('POST', url, payload, response_json, response.status_code)
            
            if response.status_code in [200, 201]:
                return {'success': True, 'data': response_json}
            else:
                error_msg = response_json.get('message') or response_json.get('error') or f"HTTP {response.status_code}"
                return {'success': False, 'error': f"Fragmently API rejected request: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            self._log_request('POST', url, payload, None, None, error_msg)
            return {'success': False, 'error': error_msg}


class TelegramOrderService:
    """Service for managing Telegram Orders"""
    
    @staticmethod
    def create_order(user, product: TelegramProduct, telegram_username: str, custom_quantity: int = None) -> tuple[TelegramOrder, str]:
        """
        Create a new Telegram order
        
        Returns: (order, error_message)
        """
        try:
            # Determine base price
            base_price = product.price_uzs
            if product.sku == 'custom_stars' and custom_quantity:
                qty = int(custom_quantity)
                if qty < 100:
                    rate = 240
                elif qty < 250:
                    rate = 220
                elif qty < 500:
                    rate = 208
                elif qty < 1000:
                    rate = 200
                elif qty < 5000:
                    rate = 190
                else:
                    rate = 180
                base_price = Decimal(qty * rate)

            # Generate unique amount and code
            unique_amount, variance = UniqueAmountGenerator.generate_unique_amount(base_price)
            unique_code = UniqueAmountGenerator.generate_unique_code()
            
            # Create order
            order = TelegramOrder.objects.create(
                user=user,
                product=product,
                telegram_username=telegram_username.lstrip('@'),
                custom_quantity=custom_quantity,
                base_price=base_price,
                unique_amount=unique_amount,
                unique_code=unique_code,
                status='waiting_payment'
            )
            
            # Create payment record
            TelegramPayment.objects.create(
                order=order,
                amount=unique_amount,
                payment_method='card_transfer'
            )
            
            # Log action
            TelegramOrderLog.objects.create(
                order=order,
                action='order_created',
                status_to='waiting_payment',
                message=f'Order created for {product.name}',
                performed_by=user,
                metadata={'variance': variance}
            )
            
            # Create notification
            TelegramNotification.objects.create(
                user=user,
                order=order,
                notification_type='order_created',
                title='Order Created',
                message=f'Your order for {product.name} has been created. Amount: {unique_amount:,.0f} UZS'
            )
            
            logger.info(f"Order {unique_code} created by {user.username}")
            return order, None
        
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None, str(e)
    
    @staticmethod
    def confirm_payment(order: TelegramOrder, admin_user, note: str = "") -> bool:
        """Confirm payment for an order"""
        try:
            order.status = 'paid'
            order.payment_confirmed_at = timezone.now()
            order.save()
            
            # Update payment
            payment = order.payment
            payment.payment_status = 'confirmed'
            payment.confirmed_by = admin_user
            payment.confirmation_note = note
            payment.confirmed_at = timezone.now()
            payment.save()
            
            # Log action
            TelegramOrderLog.objects.create(
                order=order,
                action='payment_confirmed',
                status_from='waiting_confirmation',
                status_to='paid',
                message='Payment confirmed by admin',
                performed_by=admin_user
            )
            
            # Create notification
            TelegramNotification.objects.create(
                user=order.user,
                order=order,
                notification_type='payment_confirmed',
                title='Payment Confirmed',
                message='Your payment has been confirmed. Delivery will start shortly.'
            )
            
            logger.info(f"Payment confirmed for order {order.unique_code}")
            
            # Auto-trigger delivery if enabled
            settings = TelegramSettings.objects.first()
            auto_enabled = settings.auto_delivery_enabled if settings else True
            
            if auto_enabled and order.product.auto_delivery:
                delivery_success = TelegramOrderService.process_delivery(order)
                if delivery_success:
                    TelegramOrderService.complete_order(order)
            
            return True
        
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return False
    
    @staticmethod
    def process_delivery(order: TelegramOrder) -> bool:
        """Process delivery for an order"""
        try:
            if not order.product.auto_delivery:
                return False
            
            provider = order.product.provider or TelegramProvider.objects.filter(is_active=True).first()
            if not provider:
                raise Exception("No active provider found")
            
            service = TelegramProviderService(provider)
            
            # Get user info if needed
            if not order.telegram_user_id:
                user_info = service.get_user_info(order.telegram_username)
                if user_info['success']:
                    order.telegram_user_id = user_info['data'].get('id', '')
                    order.telegram_avatar = user_info['data'].get('photo', '')
                else:
                    logger.warning(f"User lookup failed for {order.telegram_username}: {user_info.get('error')}")
            
            # Process based on product type
            result = None
            if order.product.category.name == 'stars':
                result = service.send_stars(order.telegram_username, order.custom_quantity or order.product.quantity)
            elif order.product.category.name == 'premium':
                result = service.send_premium(order.telegram_username, order.product.quantity)
            elif order.product.category.name == 'gifts':
                result = service.send_gift(order.telegram_username, order.product.provider_gift_id or '')
            
            if not result:
                raise Exception("No delivery method available")
            
            if result['success']:
                order.status = 'processing'
                order.transaction_id = result['data'].get('transaction_id', '')
                order.provider_response = result['data']
                order.save()
                
                TelegramOrderLog.objects.create(
                    order=order,
                    action='delivery_processing',
                    status_to='processing',
                    message=f'Delivery initiated via {provider.name}',
                    metadata=result.get('data', {})
                )
                
                return True
            else:
                order.delivery_attempts += 1
                order.save()
                
                TelegramOrderLog.objects.create(
                    order=order,
                    action='delivery_failed',
                    message=f'Delivery failed: {result.get("error")}'
                )
                
                raise Exception(f"Delivery failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing delivery for {order.unique_code}: {str(e)}")
            order.delivery_attempts += 1
            order.save()
            return False
    
    @staticmethod
    def complete_order(order: TelegramOrder) -> bool:
        """Mark order as completed and pay seller"""
        from django.db import transaction
        from apps.users.models import Wallet
        from .models import TelegramSettings, TelegramOrderLog, TelegramNotification
        
        # Idempotency check: Don't process twice
        if order.status == 'completed':
            logger.info(f"Telegram Order {order.unique_code} already marked as completed.")
            return True

        try:
            with transaction.atomic():
                # Refresh and lock the order row
                order = TelegramOrder.objects.select_for_update().get(pk=order.pk)
                
                # Check status again inside transaction
                if order.status == 'completed':
                    return True

                # 1. Update order status
                order.status = 'completed'
                order.completed_at = timezone.now()
                order.save(update_fields=['status', 'completed_at'])
                
                # 2. Log Action
                TelegramOrderLog.objects.create(
                    order=order,
                    action='order_completed',
                    status_to='completed',
                    message='Order completed successfully via automation'
                )
                
                # 3. Notify User
                TelegramNotification.objects.create(
                    user=order.user,
                    order=order,
                    notification_type='delivery_completed',
                    title='Xarid Yakunlandi',
                    message=f'Sizning {order.product.name} xaridingiz muvaffaqiyatli yakunlandi!'
                )
                
                # 4. Pay Seller
                if order.product and order.product.seller:
                    settings_obj = TelegramSettings.get_settings()
                    platform_comm = settings_obj.commission_percentage if settings_obj else Decimal('10.0')
                    
                    # Calculate seller's share after commission
                    seller_amount = (order.unique_amount * (Decimal('1.0') - (platform_comm / Decimal('100')))).quantize(Decimal('0.01'))
                    
                    if seller_amount > 0:
                        seller_wallet, _ = Wallet.objects.get_or_create(user=order.product.seller)
                        logger.info(f"PAYOUT: Paying {seller_amount} UZS to seller {order.product.seller.username} for Telegram order {order.unique_code}")
                        
                        # Use Wallet's atomic add_funds helper
                        seller_wallet.add_funds(
                            amount=seller_amount,
                            reason=f"Telegram Sotuv: {order.product.name} (Buyurtma #{order.unique_code})"
                        )
                    else:
                        logger.warning(f"PAYOUT: Skipping zero payout for Telegram order {order.unique_code}")
                else:
                    logger.info(f"PAYOUT: No seller found for product {order.product.sku}. Skipping payout.")

                logger.info(f"Telegram Order {order.unique_code} processed successfully.")
                return True
        
        except Exception as e:
            logger.error(f"CRITICAL ERROR in Telegram complete_order for #{order.unique_code}: {str(e)}", exc_info=True)
            return False
