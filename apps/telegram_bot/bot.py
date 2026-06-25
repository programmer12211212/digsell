import os
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from django.conf import settings
from apps.users.models import User

# Bot settings can be in environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = (
        "Digsell.uz Rasmiy botiga xush kelibsiz!\n\n"
        "Bu erda siz xaridlar haqida bildirishnomalar olishingiz va "
        "o'z profilingizni bog'lashingiz mumkin.\n"
        f"Sizning ID: {user_id}\n\n"
        "Profilingizga o'ting va ushbu ID-ni bog'lang."
    )
    await update.message.reply_text(message)

def run_bot():
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
        print("Telegram Bot Token not set!")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot started...")
    app.run_polling()

def send_telegram_notification(chat_id, text):
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
        return
    bot = Bot(token=TOKEN)
    import asyncio
    try:
        asyncio.run(bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML'))
    except Exception as e:
        print(f"Error sending telegram message: {e}")
