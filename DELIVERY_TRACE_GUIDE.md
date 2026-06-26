# Telegram Stars Delivery Pipeline - Complete Tracing Guide

## Overview
Comprehensive logging has been added to trace the entire Stars delivery pipeline from Hamyon payment confirmation through Fragment API call to order completion.

## Complete Delivery Flow with Logging

### Step-by-Step Log Entry Points

```
[STEP 1] process_payment_status
  ↓
  Payment SUCCESS detected
  ↓
  [STEP 2] process_payment_status: Calling process_related_payment()
  ↓
  
[TELEGRAM-DELIVERY-1] process_related_payment: START
  ↓
[TELEGRAM-DELIVERY-2] process_related_payment: Detected TELEGRAM_ORDER
  ↓
[TELEGRAM-DELIVERY-3] process_related_payment: Found telegram_order
  ↓
[TELEGRAM-DELIVERY-4] process_related_payment: Order in waiting_payment, calling confirm_payment()
  ↓

[TELEGRAM-DELIVERY-5] process_related_payment: confirm_payment() returned
  ↓

[TELEGRAM-DELIVERY-6] confirm_payment: START
  ↓
[TELEGRAM-DELIVERY-7] confirm_payment: Checking auto-delivery settings
  ↓
[TELEGRAM-DELIVERY-7a] confirm_payment: auto_enabled & auto_delivery check
  ↓
[TELEGRAM-DELIVERY-8] confirm_payment: Auto-delivery ENABLED, calling process_delivery()
  ↓

[TELEGRAM-DELIVERY-11] process_delivery: START
  ↓
[TELEGRAM-DELIVERY-12] process_delivery: Using provider X (api_token=True)
  ↓
[TELEGRAM-DELIVERY-13] process_delivery: Fetching user info
  ↓
[TELEGRAM-DELIVERY-14] process_delivery: Category=stars, Quantity=N, Username=@user
  ↓
[TELEGRAM-DELIVERY-15] process_delivery: Calling send_stars()
  ↓

[TELEGRAM-DELIVERY-19] send_stars: START
  ↓
[TELEGRAM-DELIVERY-20] send_stars: URL=..., is_test=False
  ↓
[TELEGRAM-DELIVERY-22] send_stars: Sending Fragment API request
  ↓
[TELEGRAM-DELIVERY-22a] send_stars: Payload: {...}
  ↓
[TELEGRAM-DELIVERY-22b] send_stars: Headers: {...}
  ↓
[TELEGRAM-DELIVERY-23] send_stars: Fragment API HTTP Status=200
  ↓
[TELEGRAM-DELIVERY-23a] send_stars: Fragment API Response: {...}
  ↓
[TELEGRAM-DELIVERY-24] send_stars: Fragment API SUCCESS
  ↓
[TELEGRAM-DELIVERY-15a] process_delivery: send_stars() returned success
  ↓
[TELEGRAM-DELIVERY-16] process_delivery: Checking result success=True
  ↓
[TELEGRAM-DELIVERY-17] process_delivery: Delivery SUCCESS! Updating to 'processing'
  ↓
[TELEGRAM-DELIVERY-18] process_delivery: DELIVERY COMPLETE - Returning True
  ↓

[TELEGRAM-DELIVERY-9] confirm_payment: process_delivery() returned True
  ↓
[TELEGRAM-DELIVERY-10] confirm_payment: Calling complete_order()
  ↓

[TELEGRAM-DELIVERY-25] complete_order: START
  ↓
[TELEGRAM-DELIVERY-26] complete_order: Updating order to 'completed'
  ↓
[TELEGRAM-DELIVERY-27] complete_order: Creating log entry
  ↓
[TELEGRAM-DELIVERY-28] complete_order: PAYOUT to seller
  ↓
[TELEGRAM-DELIVERY-FINAL] complete_order: Order SUCCESSFULLY COMPLETED
  ↓

Frontend receives order_status='completed' and shows success animation
```

## Log Categories

### 1. Payment Processing Logs
- **Location**: `apps/payments/services.py`
- **Function**: `process_payment_status()`
- **Logs**: `[STEP 1]`, `[STEP 2]`
- **Checks**:
  - Payment status SUCCESS detected
  - `process_related_payment()` called
  - Return value checked

### 2. Related Payment Processing
- **Location**: `apps/payments/services.py`
- **Function**: `process_related_payment()`
- **Logs**: `[TELEGRAM-DELIVERY-1]` to `[TELEGRAM-DELIVERY-5]`
- **Checks**:
  - Payment purpose is TELEGRAM_ORDER
  - Order exists in database
  - Order status is `waiting_payment`
  - `confirm_payment()` successfully called

### 3. Payment Confirmation
- **Location**: `apps/telegram_services/services.py`
- **Function**: `TelegramOrderService.confirm_payment()`
- **Logs**: `[TELEGRAM-DELIVERY-6]` to `[TELEGRAM-DELIVERY-10]`
- **Checks**:
  - Order status updated to `paid`
  - Auto-delivery settings enabled
  - Product has `auto_delivery=True`
  - `process_delivery()` called successfully

### 4. Delivery Processing
- **Location**: `apps/telegram_services/services.py`
- **Function**: `TelegramOrderService.process_delivery()`
- **Logs**: `[TELEGRAM-DELIVERY-11]` to `[TELEGRAM-DELIVERY-18]`
- **Critical Checks**:
  - `order.product.auto_delivery` is True
  - Provider exists and is active
  - Provider has API token
  - Product category is "stars"
  - Quantity > 0
  - `send_stars()` called

### 5. Fragment API Call
- **Location**: `apps/telegram_services/services.py`
- **Function**: `TelegramProviderService.send_stars()`
- **Logs**: `[TELEGRAM-DELIVERY-19]` to `[TELEGRAM-DELIVERY-24]`
- **Critical Info**:
  - Full request payload logged (JSON)
  - Headers logged
  - HTTP status code captured
  - Response body logged (JSON)
  - Timeout/connection errors logged with traceback

### 6. Order Completion
- **Location**: `apps/telegram_services/services.py`
- **Function**: `TelegramOrderService.complete_order()`
- **Logs**: `[TELEGRAM-DELIVERY-25]` to `[TELEGRAM-DELIVERY-FINAL]`
- **Actions**:
  - Order marked as complete
  - Seller payout calculated and applied
  - Notification created

## Error Logs

All errors are prefixed with `[TELEGRAM-DELIVERY-ERROR]` or `[TELEGRAM-DELIVERY-CRITICAL-ERROR]`

### Critical Errors to Watch For:
1. `[TELEGRAM-DELIVERY-ERROR] process_related_payment: TelegramOrder NOT FOUND`
   - **Issue**: Order doesn't exist in database
   - **Action**: Check order_id and user association

2. `[TELEGRAM-DELIVERY-ERROR] process_delivery: Product auto_delivery is FALSE`
   - **Issue**: Product has auto_delivery disabled
   - **Action**: Enable auto_delivery for product

3. `[TELEGRAM-DELIVERY-ERROR] process_delivery: No provider found`
   - **Issue**: No active provider configured
   - **Action**: Create/activate TelegramProvider

4. `[TELEGRAM-DELIVERY-ERROR] send_stars: API token missing`
   - **Issue**: Provider API token not set
   - **Action**: Configure provider API token

5. `[TELEGRAM-DELIVERY-ERROR] send_stars: Fragment API HTTP 400/401/403/500`
   - **Issue**: Fragment API rejected request
   - **Action**: Check API credentials, payload, Fragment API status

6. `[TELEGRAM-DELIVERY-ERROR] send_stars: Fragment API timeout`
   - **Issue**: Fragment API didn't respond within 10 seconds
   - **Action**: Check network, Fragment API uptime

## How to Use This Tracing

### 1. Monitor During Payment
Watch for these log sequences in real-time:
```bash
# Terminal running Django server
cd c:\Users\User\Desktop\digsell\digsell\digsell\platforma\ (2)\ (2)\platforma\ (2)\platforma
python manage.py runserver
```

### 2. Trigger a Test Payment
- Create a test order
- Initiate Hamyon payment via UI
- Wait for payment flow

### 3. Check Logs in Order
Follow the log sequence above. Each step should complete before next begins.

### 4. If Stuck at Any Step
- Find the corresponding `[TELEGRAM-DELIVERY-N]` log
- Look for error logs immediately after
- Check the specific conditions listed in that section

### 5. Extract Logs to File
```bash
# Capture to file for analysis
python manage.py runserver > delivery_trace.log 2>&1
```

## Testing Fragment API Directly

If logs show Fragment API fails, test directly:

```python
import requests

# Test Fragment API endpoint
provider_token = "YOUR_PROVIDER_API_KEY"
url = "https://fragment-api.com/api/v1/buy-stars/"

payload = {
    "query": "@telegram_username",
    "quantity": 10,
    "payment_method": "ton",
    "wallet_version": "V4R2"
}

headers = {
    "Authorization": f"Bearer {provider_token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## Frontend Status Updates

The frontend polls for `order_status`:
- `waiting_payment` → `paid` → `processing` → `completed`
- Each status change triggers UI update
- On `completed`, shows success animation and redirects

When you see "Avtomatik yetkazish davom etmoqda..." (Automatic delivery in progress), check logs for:
1. Is `send_stars()` being called? (Look for `[TELEGRAM-DELIVERY-19]`)
2. Is Fragment API responding? (Look for `[TELEGRAM-DELIVERY-23]`)
3. Is response success=True? (Look for `[TELEGRAM-DELIVERY-24]`)
4. Is order being marked as processing? (Look for `[TELEGRAM-DELIVERY-17]`)
5. Is complete_order being called? (Look for `[TELEGRAM-DELIVERY-25]`)

## Database Schema Check

Verify these fields exist on TelegramOrder model:
- `status` (CharField: waiting_payment, paid, processing, completed)
- `auto_delivery` (on TelegramProduct, not order)
- `provider_response` (JSONField, stores Fragment API response)
- `transaction_id` (CharField, stores Fragment transaction ID)

## Performance Notes
- All logging is minimal overhead
- Fragment API timeout is 10 seconds
- Process should complete in < 15 seconds after payment

## Files Modified
1. `apps/payments/services.py` - process_payment_status(), process_related_payment()
2. `apps/telegram_services/services.py` - confirm_payment(), process_delivery(), send_stars(), complete_order()
