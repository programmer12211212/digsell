# Quick Delivery Diagnosis Checklist

## Run This to Capture Logs

```bash
cd "c:\Users\User\Desktop\digsell\digsell\digsell\platforma (2) (2)\platforma (2)\platforma"
python manage.py runserver 2>&1 | tee delivery_logs.txt
```

Then trigger a test payment and run through the flow.

---

## Diagnosis Flowchart

### Issue: "Avtomatik yetkazish davom etmoqda..." (stuck forever)

1. **Did logs show `[TELEGRAM-DELIVERY-1]`?**
   - NO → Payment not detected as SUCCESS. Check Hamyon response in logs BEFORE `[TELEGRAM-DELIVERY-1]`
   - YES → Go to step 2

2. **Did logs show `[TELEGRAM-DELIVERY-6]`?**
   - NO → confirm_payment() not called. Check `[STEP 2]` log - did process_related_payment() return True?
   - YES → Go to step 3

3. **Did logs show `[TELEGRAM-DELIVERY-7a]`?**
   - NO → Exception occurred in confirm_payment(). Check for `[TELEGRAM-DELIVERY-ERROR]` in logs
   - YES → Go to step 4

4. **Does `[TELEGRAM-DELIVERY-7a]` log show BOTH `auto_enabled=True` AND `auto_delivery=True`?**
   - NO (one or both False) → Auto-delivery is DISABLED. Enable in admin settings.
   - YES → Go to step 5

5. **Did logs show `[TELEGRAM-DELIVERY-11]`?**
   - NO → process_delivery() not called. Check step 4 result again.
   - YES → Go to step 6

6. **Did logs show `[TELEGRAM-DELIVERY-12]` with `api_token=True`?**
   - NO (`api_token=False` or no log) → Provider missing or has no API token
   - YES → Go to step 7

7. **Did logs show `[TELEGRAM-DELIVERY-14]` with `Category=stars`?**
   - NO (`Category=premium/gifts`) → Wrong product category
   - NOT SHOWN → process_delivery() exited early, check error logs
   - YES → Go to step 8

8. **Did logs show `[TELEGRAM-DELIVERY-19]`?**
   - NO → send_stars() not called. Check `[TELEGRAM-DELIVERY-15]` - did process_delivery() decide not to call send_stars()?
   - YES → Go to step 9

9. **Did logs show `[TELEGRAM-DELIVERY-22]`?**
   - NO → Error in send_stars() validation. Check `[TELEGRAM-DELIVERY-ERROR]` logs.
   - YES → Go to step 10

10. **Did logs show `[TELEGRAM-DELIVERY-23]` with `HTTP Status=200`?**
    - NO (4xx/5xx) → Fragment API rejected request. Check error in `[TELEGRAM-DELIVERY-23a]`
    - NO (Timeout) → Fragment API unreachable, network issue
    - YES → Go to step 11

11. **Did logs show `[TELEGRAM-DELIVERY-24] Fragment API SUCCESS`?**
    - NO → Response parsed as failure. Check `[TELEGRAM-DELIVERY-23a]` for exact response
    - YES → Go to step 12

12. **Did logs show `[TELEGRAM-DELIVERY-FINAL] Order SUCCESSFULLY COMPLETED`?**
    - NO → Order not marked completed. Check logs after `[TELEGRAM-DELIVERY-25]` for error
    - YES → **DELIVERY SUCCESSFUL!** Frontend should show success. Check if frontend polling detected order_status=completed

---

## Key Data to Capture

When you provide delivery logs, please include:

### For Each Step Found, Note:
- **Log marker number** (e.g., `[TELEGRAM-DELIVERY-6]`)
- **Exact text** after the marker
- **Timestamp** (if visible)

### If Error Found, Capture:
- The `[TELEGRAM-DELIVERY-ERROR]` or `[TELEGRAM-DELIVERY-CRITICAL-ERROR]` line
- The 3 lines BEFORE the error (context)
- The 3 lines AFTER the error (what was being attempted)
- Any exception traceback after the error log

### For Fragment API Issues, Capture:
- `[TELEGRAM-DELIVERY-22a]` - The exact payload sent
- `[TELEGRAM-DELIVERY-22b]` - The exact headers sent
- `[TELEGRAM-DELIVERY-23]` - HTTP status code
- `[TELEGRAM-DELIVERY-23a]` - The exact response received

---

## Common Issues & Fixes

| Issue | Look For | Fix |
|-------|----------|-----|
| Auto-delivery disabled | `[TELEGRAM-DELIVERY-7a] auto_enabled=False` | Django admin → TelegramSettings → enable auto_delivery |
| Auto-delivery disabled | `[TELEGRAM-DELIVERY-7a] auto_delivery=False` | Django admin → Product → enable auto_delivery |
| No provider | `[TELEGRAM-DELIVERY-12] No provider found` | Create active TelegramProvider in Django admin |
| No API token | `[TELEGRAM-DELIVERY-ERROR] API token missing` | Set api_token field on TelegramProvider |
| Wrong category | `[TELEGRAM-DELIVERY-14] Category=premium` | Product category must be 'stars' not 'premium'/'gifts' |
| Fragment API 401 | `[TELEGRAM-DELIVERY-23] HTTP Status=401` | Check API token is correct and not expired |
| Fragment API unreachable | `[TELEGRAM-DELIVERY-ERROR] Timeout` | Check network, Fragment API uptime |
| Order not updated | `[TELEGRAM-DELIVERY-17]` missing | Check database permissions, order.save() errors |

---

## Test With This Script

Create a test script in Django shell:

```python
from apps.telegram_services.models import TelegramOrder, TelegramProvider, TelegramProduct
from apps.telegram_services.services import TelegramOrderService

# Find your test order
order = TelegramOrder.objects.get(unique_code="YOUR_ORDER_CODE")

# Check settings
print(f"Order status: {order.status}")
print(f"Product auto_delivery: {order.product.auto_delivery}")
print(f"Product category: {order.product.category.name}")

# Check provider
provider = order.product.provider or TelegramProvider.objects.filter(is_active=True).first()
print(f"Provider: {provider}")
print(f"Provider active: {provider.is_active if provider else 'NO PROVIDER'}")
print(f"Provider has API token: {bool(provider.api_token) if provider else False}")

# Try delivery manually
try:
    result = TelegramOrderService.process_delivery(order)
    print(f"process_delivery() returned: {result}")
except Exception as e:
    print(f"process_delivery() exception: {e}")
    import traceback
    traceback.print_exc()
```

---

## Frontend Polling Expected Behavior

Frontend polls `/telegram-services/orders/{order_id}/check-hamyon-status/` every 2-5 seconds.

Expected responses:
1. `{"status": "PENDING", "order_status": "waiting_payment", ...}` - waiting
2. `{"status": "SUCCESS", "order_status": "paid", ...}` - payment confirmed, delivery starting
3. `{"status": "SUCCESS", "order_status": "processing", ...}` - delivery in progress
4. `{"status": "SUCCESS", "order_status": "completed", ...}` - finished!

If frontend shows step 2 forever ("Avtomatik yetkazish davom etmoqda...") and backend sees step 4 ("Bajarildi"), it means:
- **Backend**: Delivery completed successfully
- **Frontend**: Not detecting the completion
- **Issue**: Frontend polling not updating after delivery complete, or order_status not returned in API response

Check `/apps/telegram_services/views.py` line 548 - `check_hamyon_payment_status()` must include `order_status` in response.
