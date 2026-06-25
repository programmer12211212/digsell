import requests
from django.conf import settings

from apps.core.utils import format_uzs

class TelegramBot:
    def __init__(self):
        self.token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.api_url = f"https://api.telegram.org/bot{self.token}/"

    def send_message(self, chat_id, text, parse_mode="HTML"):
        if not self.token:
            return None
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            response = requests.post(self.api_url + "sendMessage", json=payload)
            return response.json()
        except Exception as e:
            print(f"Telegram Error: {e}")
            return None

    def send_order_notification(self, user, order):
        if not user.telegram_id:
            return
            
        text = (
            f"<b>Yangi Buyurtma!</b> 🚀\n\n"
            f"Mahsulot: {order.product.title}\n"
            f"Narxi: {format_uzs(order.amount)}\n"
            f"Holat: {order.status}\n\n"
            f"Tabriklaymiz!"
        )
        self.send_message(user.telegram_id, text)

    def send_login_alert(self, user, ip):
        if not user.telegram_id:
            return
            
        text = (
            f"<b>Xavfsizlik Ogohlantirishi!</b> ⚠️\n\n"
            f"Hisobingizga yangi kirish aniqlandi.\n"
            f"IP: {ip}\n"
            f"Agar bu siz bo'lmasangiz, darhol parolni o'zgartiring."
        )
        self.send_message(user.telegram_id, text)
