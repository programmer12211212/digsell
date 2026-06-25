import requests
from django.conf import settings

def send_telegram_notification(user, message):
    """
    Sends a formatted notification to the user via Telegram.
    Requires user.telegram_id to be set.
    """
    if not user.telegram_id:
        return False

    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": user.telegram_id,
        "text": f"🔔 *Digsell.uz BILDIRISHNOMA*\n\n{message}",
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def alert_admins_of_payment(order):
    """
    Alerts the system admins via Telegram about a new payment receipt.
    """
    # implementation for admin-specific group chat etc.
    pass
