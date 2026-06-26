import random
import string
import requests
import logging
import os
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum
from django.core.cache import cache
from django.conf import settings
from .models import (
    TelegramOrder, TelegramPayment, TelegramProvider, 
    TelegramProviderLog, TelegramOrderLog, TelegramNotification,
    TelegramSettings, TelegramProduct, TelegramRewardCampaign,
    TelegramRewardStage, TelegramRewardClaim
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
    def generate_unique_amount(base_amount: Decimal, min_variance: int = 1, max_variance: int = 99):
        """
        Generate unique amount by adding random variance
        
        Example: 12000 → 12038, 12092, 12015
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
            'Accept': 'application/json'
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
            self._log_request('GET', f"{self.base_url}/balance", {}, res_data, 200)
            return {'success': True, 'data': res_data}
            
        try:
            url = f"{self.base_url}/balance"
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
            self._log_request('GET', f"{self.base_url}/balance", {}, None, None, error_msg)
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
            self._log_request('GET', f"{self.base_url}/balance", {}, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            url = f"{self.base_url}/balance"
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
            self._log_request('GET', f"{self.base_url}/balance", {}, None, None, error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_user_info(self, telegram_username: str) -> dict:
        """Get Telegram user info"""
        logger.info(f"STEP 4c: get_user_info START for @{telegram_username}")
        if not self.provider.api_token:
            logger.error(f"Returning because API token missing for provider {self.provider.id}")
            return {'success': False, 'error': 'API token missing'}
            
        if not telegram_username:
            logger.error("Returning because telegram_username is missing")
            return {'success': False, 'error': 'Username is required'}
            
        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"
        url = f"{self.base_url}/info/"
        params = {'query': username}
        
        if self.provider.is_test:
            logger.info("STEP 4d-MOCK: Returning mock user info")
            res_data = {
                'id': '765432109',
                'username': username.lstrip('@'),
                'first_name': 'Sotdim User',
                'last_name': 'Test',
                'photo': f'https://ui-avatars.com/api/?name={username.lstrip("@")}&background=0ea5e9&color=fff'
            }
            self._log_request('GET', url, params, res_data, 200)
            return {'success': True, 'data': res_data}

        try:
            logger.info(f"STEP 4e: Requesting Fragment API INFO URL={url} with params={params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            logger.info(f"STEP 4f: [FRAGMENT-INFO-RESPONSE] HTTP {response.status_code}")
            
            try:
                response_json = response.json()
                logger.info(f"STEP 4g: Decoded Info JSON: {response_json}")
            except ValueError:
                response_json = {"raw_response": response.text}
                logger.warning(f"Returning because Fragment API info returned non-JSON: {response.text}")
                
            self._log_request('GET', url, params, response_json, response.status_code)
            
            if response.status_code == 200:
                logger.info(f"STEP 4h: get_user_info SUCCESS for @{telegram_username}")
                return {'success': True, 'data': response_json}
            else:
                logger.error(f"Returning because Fragment API info REJECTED: HTTP {response.status_code}, Body: {response.text}")
                return {'success': False, 'error': f"User not found or HTTP {response.status_code}"}
        except Exception as e:
            import traceback
            logger.error(f"Returning because unexpected error in Fragment info request: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def send_stars(self, telegram_username: str, quantity: int) -> dict:
        """Send Telegram Stars"""
        from .delivery_pipeline_trace import get_trace

        logger.info("ENTER send_stars")
        get_trace().mark_reached('send_stars')
        logger.info(
            "telegram_username=%s | stars_quantity=%s | provider=%s | provider_enabled=%s",
            telegram_username,
            quantity,
            getattr(self.provider, 'name', None),
            getattr(self.provider, 'is_active', None),
        )

        if not self.provider.api_token:
            get_trace().mark_stopped('send_stars', 'API token missing')
            logger.info("RETURN because API token missing for provider %s", self.provider.id)
            return {'success': False, 'error': 'API token missing'}

        if not telegram_username:
            get_trace().mark_stopped('send_stars', 'telegram_username is empty')
            logger.info("RETURN because telegram_username is empty")
            return {'success': False, 'error': 'Username is required'}

        username = telegram_username if telegram_username.startswith('@') else f"@{telegram_username}"

        try:
            qty = int(quantity)
            if qty <= 0:
                get_trace().mark_stopped('send_stars', f'quantity {qty} must be > 0')
                logger.info("RETURN because quantity %s must be > 0", qty)
                return {'success': False, 'error': 'Quantity must be greater than 0'}
        except (ValueError, TypeError) as e:
            get_trace().mark_stopped('send_stars', f'quantity {quantity!r} is invalid: {e}')
            logger.info("RETURN because quantity %r is invalid: %s", quantity, e)
            return {'success': False, 'error': 'Quantity must be integer'}

        payload = {
            "query": username,
            "quantity": qty,
            "payment_method": "ton",
            "wallet_version": "V4R2"
        }

        url = f"{self.base_url}/buy-stars/"
        endpoint = url

        if self.provider.is_test:
            logger.info("RETURN because provider.is_test=True (mock response, Fragment API NOT called)")
            import uuid
            res_data = {
                'transaction_id': f'txn_stars_{uuid.uuid4().hex[:12]}',
                'status': 'delivered',
                'query': username,
                'quantity': qty
            }
            self._log_request('POST', url, payload, res_data, 200)
            return {'success': True, 'data': res_data}

        logger.info("Fragment API request:")
        logger.info("  Endpoint: %s", endpoint)
        logger.info("  Username: %s", username)
        logger.info("  Stars quantity: %s", qty)
        logger.info("  Provider: %s", getattr(self.provider, 'name', None))
        logger.info("  Request payload: %s", payload)
        logger.info("  Headers: %s", self.headers)

        try:
            get_trace().fragment_api_called = True
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)

            raw_response = response.text
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw_response": raw_response}

            get_trace().mark_fragment_response(response.status_code, raw_response, response_json)

            logger.info("Fragment API response:")
            logger.info("  HTTP status: %s", response.status_code)
            logger.info("  Raw response: %s", raw_response)
            logger.info("  JSON response: %s", response_json)

            self._log_request('POST', url, payload, response_json, response.status_code)

            if response.status_code in [200, 201]:
                logger.info("RETURN send_stars success for %s", username)
                return {'success': True, 'data': response_json}

            error_msg = response_json.get('message') or response_json.get('error') or f"HTTP {response.status_code}"
            get_trace().mark_stopped('send_stars', f'Fragment API rejected: {error_msg}')
            logger.info("RETURN because Fragment API rejected: %s", error_msg)
            return {'success': False, 'error': f"Fragmently API rejected request: {error_msg}"}
        except requests.exceptions.Timeout as e:
            get_trace().mark_stopped('send_stars', 'Fragment API timeout (10s)')
            import traceback
            logger.error("EXCEPTION in send_stars: Timeout: %s", e)
            logger.error(traceback.format_exc())
            return {'success': False, 'error': "Provider timeout (10s)"}
        except requests.exceptions.ConnectionError as e:
            get_trace().mark_stopped('send_stars', f'Fragment API connection error: {e}')
            import traceback
            logger.error("EXCEPTION in send_stars: ConnectionError: %s", e)
            logger.error(traceback.format_exc())
            return {'success': False, 'error': f"Provider unavailable: {str(e)}"}
        except Exception as e:
            get_trace().mark_stopped('send_stars', f'unexpected error: {type(e).__name__}: {e}')
            import traceback
            logger.error("EXCEPTION in send_stars: %s: %s", type(e).__name__, e)
            logger.error(traceback.format_exc())
            return {'success': False, 'error': f"Provider unavailable: {str(e)}"}
    
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
            "quantity": qty,
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
    def confirm_payment(
        order: TelegramOrder,
        admin_user,
        note: str = "",
        payment_method: str = None,
        transaction_id: str = None,
    ) -> bool:
        """Confirm payment for an order"""
        from .delivery_pipeline_trace import get_trace, log_order_context

        logger.info("ENTER confirm_payment")
        get_trace().mark_reached('confirm_payment')
        log_order_context(order, prefix='confirm_payment')

        try:
            previous_status = order.status
            if order.status in ['paid', 'processing', 'completed']:
                get_trace().mark_stopped(
                    'confirm_payment',
                    f'order already in status={order.status}; process_delivery SKIPPED (early return)',
                )
                logger.info(
                    "RETURN because order already in status=%s; process_delivery SKIPPED",
                    order.status,
                )
                payment = order.payment
                if payment.payment_status != 'confirmed':
                    logger.info("Updating existing payment status to 'confirmed'")
                    payment.payment_status = 'confirmed'
                    payment.confirmed_by = admin_user
                    payment.confirmation_note = note
                    payment.confirmed_at = timezone.now()
                    if payment_method:
                        payment.payment_method = payment_method
                    payment.save(update_fields=[
                        'payment_status', 'confirmed_by', 'confirmation_note', 'confirmed_at', 'payment_method',
                    ])
                return True

            logger.info("Updating order status waiting_payment -> paid")
            order.status = 'paid'
            order.payment_confirmed_at = timezone.now()
            if payment_method:
                order.payment_method = payment_method
            if transaction_id:
                order.transaction_id = transaction_id
            order.save(update_fields=[
                'status', 'payment_confirmed_at', 'payment_method', 'transaction_id',
            ])

            payment = order.payment
            payment.payment_status = 'confirmed'
            payment.confirmed_by = admin_user
            payment.confirmation_note = note
            payment.confirmed_at = timezone.now()
            if payment_method:
                payment.payment_method = payment_method
            payment.save(update_fields=[
                'payment_status', 'confirmed_by', 'confirmation_note', 'confirmed_at', 'payment_method',
            ])

            TelegramOrderLog.objects.create(
                order=order,
                action='payment_confirmed',
                status_from=previous_status,
                status_to='paid',
                message='Payment confirmed' if previous_status != 'waiting_payment' else 'Payment confirmed via Hamyon auto-flow',
                performed_by=admin_user
            )

            settings_obj = TelegramSettings.objects.first()
            auto_enabled_global = settings_obj.auto_delivery_enabled if settings_obj else True
            product_auto_delivery = order.product.auto_delivery
            is_gift_order = order.product.category.name.lower() == 'gifts'

            logger.info(
                "auto_delivery check: global_enabled=%s | product.auto_delivery=%s | is_gift=%s",
                auto_enabled_global,
                product_auto_delivery,
                is_gift_order,
            )

            if is_gift_order:
                logger.info("Skipping automatic delivery for gift order; payment is confirmed and order remains pending manual delivery.")
                TelegramOrderLog.objects.create(
                    order=order,
                    action='delivery_skipped',
                    status_from=previous_status,
                    status_to='paid',
                    message='Gift order payment confirmed; manual delivery is required.',
                    performed_by=admin_user,
                )
                get_trace().mark_stopped('confirm_payment', 'gift order - auto-delivery skipped')
                return True

            if auto_enabled_global and product_auto_delivery:
                logger.info("Calling process_delivery from confirm_payment")
                try:
                    delivery_success = TelegramOrderService.process_delivery(order)
                    logger.info("process_delivery returned %s", delivery_success)
                    if delivery_success:
                        TelegramOrderService.complete_order(order)
                        logger.info("RETURN confirm_payment success (delivery + complete_order)")
                        return True
                    get_trace().mark_stopped('confirm_payment', 'process_delivery returned False')
                    logger.info("RETURN because process_delivery returned False")
                    return False
                except Exception as e:
                    get_trace().mark_stopped('confirm_payment', f'process_delivery raised {type(e).__name__}: {e}')
                    import traceback
                    logger.error("EXCEPTION in process_delivery from confirm_payment: %s: %s", type(e).__name__, e)
                    logger.error(traceback.format_exc())
                    return False

            get_trace().mark_stopped(
                'confirm_payment',
                f'auto-delivery skipped: global_enabled={auto_enabled_global}, product.auto_delivery={product_auto_delivery}',
            )
            logger.info(
                "RETURN because auto-delivery skipped: global_enabled=%s, product.auto_delivery=%s",
                auto_enabled_global,
                product_auto_delivery,
            )
            return True

        except Exception as e:
            get_trace().mark_stopped('confirm_payment', f'unexpected error: {type(e).__name__}: {e}')
            import traceback
            logger.error("EXCEPTION in confirm_payment: %s: %s", type(e).__name__, e)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def process_delivery(order: TelegramOrder) -> bool:
        """Process delivery for an order"""
        from .delivery_pipeline_trace import get_trace, log_order_context

        logger.info("ENTER process_delivery")
        get_trace().mark_reached('process_delivery')
        log_order_context(order, prefix='process_delivery')

        try:
            if not order.product.auto_delivery:
                get_trace().mark_stopped('process_delivery', 'auto_delivery=False')
                logger.info("RETURN because auto_delivery=False")
                return False

            provider = order.product.provider or TelegramProvider.objects.filter(is_active=True).first()
            if not provider:
                get_trace().mark_stopped('process_delivery', 'provider is None')
                logger.info("RETURN because provider is None")
                return False

            logger.info(
                "provider=%s | provider_enabled=%s",
                provider.name,
                provider.is_active,
            )

            service = TelegramProviderService(provider)

            if not order.telegram_user_id:
                logger.info("telegram_user_id is empty; fetching via get_user_info")
                user_info = service.get_user_info(order.telegram_username)
                if user_info['success']:
                    order.telegram_user_id = user_info['data'].get('id', '')
                    order.telegram_avatar = user_info['data'].get('photo', '')
                    logger.info("Resolved telegram_user_id=%s", order.telegram_user_id)
                else:
                    logger.info(
                        "get_user_info failed (%s); proceeding without telegram_user_id",
                        user_info.get('error'),
                    )
            else:
                logger.info("telegram_user_id already set: %s", order.telegram_user_id)

            result = None
            category_name = order.product.category.name.lower()
            quantity = order.custom_quantity or order.product.quantity

            logger.info(
                "product.category=%s | recipient=%s | stars_quantity=%s",
                category_name,
                order.telegram_username,
                quantity,
            )

            if category_name == 'stars':
                logger.info("Calling send_stars(username=%s, quantity=%s)", order.telegram_username, quantity)
                result = service.send_stars(order.telegram_username, quantity)
                logger.info("send_stars returned success=%s", result.get('success') if result else None)
            elif category_name == 'premium':
                logger.info("Calling send_premium(username=%s, quantity=%s)", order.telegram_username, quantity)
                result = service.send_premium(order.telegram_username, quantity)
                logger.info("send_premium returned success=%s", result.get('success') if result else None)
            elif category_name == 'gifts':
                logger.info("Calling send_gift(username=%s)", order.telegram_username)
                result = service.send_gift(order.telegram_username, order.product.provider_gift_id or '')
                logger.info("send_gift returned success=%s", result.get('success') if result else None)
            else:
                get_trace().mark_stopped('process_delivery', f"product category is not stars/premium/gifts: {category_name!r}")
                logger.info("RETURN because product category is not stars/premium/gifts: %r", category_name)
                return False

            if not result:
                get_trace().mark_stopped('process_delivery', 'provider call returned None')
                logger.info("RETURN because provider call returned None")
                return False

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
                logger.info("RETURN process_delivery success; order.status=processing")
                return True

            reason = result.get('error', 'Unknown API error')
            get_trace().mark_stopped('process_delivery', f'delivery API rejected: {reason}')
            logger.info("RETURN because delivery API rejected: %s", reason)
            order.delivery_attempts += 1
            order.save()

            TelegramOrderLog.objects.create(
                order=order,
                action='delivery_failed',
                message=f'Delivery failed: {reason}'
            )
            return False

        except Exception as e:
            get_trace().mark_stopped('process_delivery', f'exception: {type(e).__name__}: {e}')
            import traceback
            logger.error("EXCEPTION in process_delivery: %s: %s", type(e).__name__, e)
            logger.error(traceback.format_exc())
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
        logger.info(f"[TELEGRAM-DELIVERY-25] complete_order: START for order {order.id} ({order.unique_code}), current status={order.status}")
        
        if order.status == 'completed':
            logger.info(f"[TELEGRAM-DELIVERY-INFO] complete_order: Order already completed, returning True")
            return True

        try:
            with transaction.atomic():
                # Refresh and lock the order row
                order = TelegramOrder.objects.select_for_update().get(pk=order.pk)
                
                # Check status again inside transaction
                if order.status == 'completed':
                    logger.info(f"[TELEGRAM-DELIVERY-INFO] complete_order: Order completed by another process, returning True")
                    return True

                # 1. Update order status
                logger.info(f"[TELEGRAM-DELIVERY-26] complete_order: Updating order status to 'completed'")
                order.status = 'completed'
                order.completed_at = timezone.now()
                order.save(update_fields=['status', 'completed_at'])
                
                logger.info(f"[TELEGRAM-DELIVERY-27] complete_order: Order marked as completed. Creating log entry.")
                
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
                        logger.info(f"[TELEGRAM-DELIVERY-28] complete_order: PAYOUT {seller_amount} UZS to seller {order.product.seller.username}")
                        
                        # Use Wallet's atomic add_funds helper
                        seller_wallet.add_funds(
                            amount=seller_amount,
                            reason=f"Telegram Sotuv: {order.product.name} (Buyurtma #{order.unique_code})"
                        )
                    else:
                        logger.warning(f"[TELEGRAM-DELIVERY-WARNING] complete_order: Skipping zero payout for order {order.unique_code}")
                else:
                    logger.info(f"[TELEGRAM-DELIVERY-INFO] complete_order: No seller found for product. Skipping payout.")

                logger.info(f"[TELEGRAM-DELIVERY-FINAL] complete_order: Order {order.unique_code} SUCCESSFULLY COMPLETED")
                logger.info("Delivery completed for order %s", order.unique_code)
                return True
        
        except Exception as e:
            logger.exception(f"[TELEGRAM-DELIVERY-CRITICAL-ERROR] complete_order: CRITICAL ERROR for order {order.unique_code}: {type(e).__name__}: {str(e)}")
            return False


class TelegramRewardService:
    """Reward track calculations and claim processing."""

    AUTO_GRANT_TYPES = ['bonus_balance', 'cashback', 'bonus_points']

    @staticmethod
    def get_active_campaign():
        now = timezone.now()
        return TelegramRewardCampaign.objects.filter(
            is_active=True
        ).filter(
            Q(start_date__lte=now) | Q(start_date__isnull=True),
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        ).order_by('-start_date').first()

    @staticmethod
    def compute_user_stats(user):
        orders = TelegramOrder.objects.filter(
            user=user,
            status='completed',
            product__category__name__in=['stars', 'premium']
        ).select_related('product')

        total_spent = orders.aggregate(total=Sum('unique_amount'))['total'] or Decimal('0')
        total_stars = 0
        total_premium_months = 0

        for order in orders:
            category_name = order.product.category.name
            if category_name == 'stars':
                total_stars += int(order.custom_quantity or order.product.quantity or 0)
            elif category_name == 'premium':
                total_premium_months += int(order.product.quantity or 0)

        return {
            'total_spent': total_spent,
            'stars_purchased': total_stars,
            'premium_months': total_premium_months
        }

    @staticmethod
    def is_stage_unlocked(stage, stats):
        if stage.target_type == 'total_spent':
            return stats['total_spent'] >= stage.target_value
        if stage.target_type == 'stars_purchased':
            return stats['stars_purchased'] >= int(stage.target_value)
        if stage.target_type == 'premium_months':
            return stats['premium_months'] >= int(stage.target_value)
        return False

    @staticmethod
    def get_user_stage_status(user, stage, stats):
        claim = TelegramRewardClaim.objects.filter(user=user, stage=stage).first()
        base_metric = 0
        if stage.target_type == 'total_spent':
            base_metric = stats['total_spent']
        elif stage.target_type == 'stars_purchased':
            base_metric = stats['stars_purchased']
        elif stage.target_type == 'premium_months':
            base_metric = stats['premium_months']

        try:
            progress = float(min(base_metric / stage.target_value, 1.0) * 100) if stage.target_value > 0 else 100.0
        except Exception:
            progress = 0.0

        return {
            'claim': claim,
            'unlocked': TelegramRewardService.is_stage_unlocked(stage, stats),
            'claimed': bool(claim and claim.status == TelegramRewardClaim.ClaimStatus.APPROVED),
            'pending': bool(claim and claim.status == TelegramRewardClaim.ClaimStatus.PENDING),
            'denied': bool(claim and claim.status == TelegramRewardClaim.ClaimStatus.DENIED),
            'can_claim': (TelegramRewardService.is_stage_unlocked(stage, stats) and claim is None),
            'progress': round(progress, 0),
        }

    @staticmethod
    def create_reward_claim(user, stage, telegram_username=None):
        stats = TelegramRewardService.compute_user_stats(user)

        if not stage.campaign.is_active or not stage.campaign.is_live:
            return None, 'Reward campaign is not active.'

        if TelegramRewardClaim.objects.filter(user=user, stage=stage).exists():
            return None, 'Siz bu bosqichni allaqachon talab qildingiz.'

        if not TelegramRewardService.is_stage_unlocked(stage, stats):
            return None, 'Siz hali bu bosqichni ochmagansiz.'

        if not telegram_username:
            return None, 'Telegram username kiriting.'

        claim = TelegramRewardClaim.objects.create(
            user=user,
            campaign=stage.campaign,
            stage=stage,
            reward_type=stage.reward_type,
            reward_amount=stage.reward_amount,
            reward_description=stage.reward_description,
            status=TelegramRewardClaim.ClaimStatus.PENDING,
            admin_note=f'Telegram username: {telegram_username}'
        )

        return claim, None

    @staticmethod
    def grant_reward(claim):
        try:
            from apps.users.models import Wallet

            wallet, _ = Wallet.objects.get_or_create(user=claim.user)
            if claim.reward_type in ['bonus_balance', 'cashback', 'bonus_points']:
                wallet.add_bonus_funds(
                    amount=claim.reward_amount,
                    reason=f"Telegram sovrin: {claim.stage.title}"
                )
                claim.reward_granted = True
                claim.save(update_fields=['reward_granted'])
                return True

            return False
        except Exception as e:
            logger.error(f"Error granting reward for claim {claim.id}: {str(e)}")
            return False

    @staticmethod
    def approve_reward_claim(claim, admin_user, note=''): 
        if claim.status != TelegramRewardClaim.ClaimStatus.PENDING:
            return False

        claim.status = TelegramRewardClaim.ClaimStatus.APPROVED
        claim.processed_at = timezone.now()
        claim.processed_by = admin_user
        if note:
            claim.admin_note = note
        claim.save(update_fields=['status', 'processed_at', 'processed_by', 'admin_note'])

        if claim.reward_type in TelegramRewardService.AUTO_GRANT_TYPES:
            TelegramRewardService.grant_reward(claim)

        return True

    @staticmethod
    def deny_reward_claim(claim, admin_user, note=''):
        if claim.status != TelegramRewardClaim.ClaimStatus.PENDING:
            return False

        claim.status = TelegramRewardClaim.ClaimStatus.DENIED
        claim.processed_at = timezone.now()
        claim.processed_by = admin_user
        if note:
            claim.admin_note = note
        claim.save(update_fields=['status', 'processed_at', 'processed_by', 'admin_note'])
        return True
