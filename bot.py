import hashlib
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from supabase import create_client, Client

# === НАСТРОЙКИ ===
BOT_TOKEN = "8412170442:AAHUHyeYyKzkjIhOZHhBArAL91oxov8i3p0"
SUPABASE_URL = "https://iqbxfnrzpsptzregcexp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxYnhmbnJ6cHNwdHpyZWdjZXhwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzNTk3MzcsImV4cCI6MjA5NTkzNTczN30.HDmiw21c7QDVjbKwJs1fuDsvWR7e21ycpv8yPpLbm_I"
CHANNEL_ID = "@winlexvpn"
PREMIUM_HOURS = 24

# === БАЗА ДАННЫХ ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === КОМАНДА /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    keyboard = [[InlineKeyboardButton("🔓 Получить Premium (24 часа)", callback_data="get_premium")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🌀 *WinLex VPN*\n\n"
        f"Привет, {user_name}!\n\n"
        f"Нажми кнопку ниже чтобы получить *{PREMIUM_HOURS} часа* Premium бесплатно.\n\n"
        f"📢 Канал: {CHANNEL_ID}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# === КНОПКА "ПОЛУЧИТЬ PREMIUM" ===
async def get_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or "no_username"

    timestamp = int(time.time())
    premium_key = hashlib.sha256(f"{user_id}{timestamp}winlex".encode()).hexdigest()[:32]
    expires_at = datetime.fromtimestamp(timestamp + PREMIUM_HOURS * 3600)

    supabase.table("users").upsert({
        "user_id": str(user_id),
        "username": username,
        "premium_key": premium_key,
        "premium_expires": expires_at.isoformat(),
        "last_used": datetime.now().isoformat()
    }, on_conflict="user_id").execute()

    await query.edit_message_text(
        f"✅ *Premium активирован!*\n\n"
        f"🔑 Ключ: `{premium_key}`\n"
        f"⏰ Длительность: *{PREMIUM_HOURS} часа*\n"
        f"📅 Истекает: *{expires_at.strftime('%H:%M %d.%m.%Y')}*\n\n"
        f"📢 Подпишись на {CHANNEL_ID}",
        parse_mode="Markdown"
    )

# === КОМАНДА /status ===
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = supabase.table("users").select("premium_key,premium_expires").eq("user_id", user_id).execute()

    if not data.data:
        await update.message.reply_text("У вас ещё нет Premium. Нажмите /start")
        return

    row = data.data[0]
    await update.message.reply_text(
        f"📊 *Статус подписки*\n\n🔑 Ключ: `{row['premium_key']}`\n📅 Истекает: {row['premium_expires']}",
        parse_mode="Markdown"
    )

# === КОМАНДА /key ===
async def show_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = supabase.table("users").select("premium_key").eq("user_id", user_id).execute()

    if not data.data or not data.data[0].get("premium_key"):
        await update.message.reply_text("У вас нет активного ключа. Нажмите /start")
        return

    await update.message.reply_text(f"🔑 Ваш ключ: `{data.data[0]['premium_key']}`", parse_mode="Markdown")

# === ЗАПУСК ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("key", show_key))
    app.add_handler(CallbackQueryHandler(get_premium, pattern="get_premium"))
    print("✅ WinLex VPN бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()