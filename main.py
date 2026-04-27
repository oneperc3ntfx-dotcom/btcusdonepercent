import os
import asyncio
import requests
from datetime import datetime, timedelta
import pytz
import random

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID missing")

CHAT_ID = int(CHAT_ID)

TZ = pytz.timezone("Asia/Jakarta")

# ================= PRICE =================
def get_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            timeout=10
        )
        return float(r.json()["price"])
    except:
        return None

# ================= SIGNAL =================
def signal(price):

    side = random.choice(["BUY", "SELL"])

    if side == "BUY":
        tp1 = price + 400
        tp2 = price + 800
        sl  = price - 200
    else:
        tp1 = price - 400
        tp2 = price - 800
        sl  = price + 200

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    return f"""
📊 BTCUSDT SIGNAL

🕒 Time: {now}
💰 Price: {price}

📈 Direction: {side}

🎯 TP1: {tp1:.2f} (400 pips)
🎯 TP2: {tp2:.2f} (800 pips)
⛔ SL : {sl:.2f} (200 pips)

━━━━━━━━━━━━━━━━━━

⚠️ Note:
- Hindari entry saat harga tidak sesuai dengan pasar
- Hindari entry saat candle agresif
- Hindari saat news high impact
"""

# ================= AUTO LOOP (:30) =================
async def loop(app):
    while True:
        now = datetime.now(TZ)

        next_run = now.replace(minute=30, second=0, microsecond=0)
        if now.minute >= 30:
            next_run = (now + timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)

        await asyncio.sleep((next_run - now).total_seconds())

        price = get_price()
        if not price:
            continue

        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=signal(price)
        )

        print("✅ Auto signal sent")

# ================= MANUAL SIGNAL =================
async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = get_price()
    if not price:
        return await update.message.reply_text("❌ Gagal ambil harga")

    await update.message.reply_text(signal(price))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 BTCUSDT Signal Bot Aktif\n\n"
        "Commands:\n"
        "/signal - ambil signal manual\n\n"
        "Auto signal tiap jam menit 30"
    )

# ================= POST INIT =================
async def post_init(app):
    asyncio.create_task(loop(app))
    print("🚀 Scheduler started")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", send_signal))

    app.post_init = post_init

    print("🤖 Bot Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
