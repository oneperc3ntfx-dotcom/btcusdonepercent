import os
import asyncio
import requests
from datetime import datetime, timedelta
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
import random

def signal(price):
    side = random.choice(["BUY", "SELL"])

    tp1 = price + 100 if side == "BUY" else price - 100
    tp2 = price + 150 if side == "BUY" else price - 150
    sl  = price - 50 if side == "BUY" else price + 50

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    return f"""
📊 BTCUSDT SIGNAL

🕒 {now}
💰 Price: {price}

📈 Direction: {side}

🎯 TP1: {tp1:.2f}
🎯 TP2: {tp2:.2f}
⛔ SL : {sl:.2f}
"""

# ================= AUTO LOOP =================
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

# ================= MANUAL SIGNAL (/signal) =================
async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = get_price()
    if not price:
        return await update.message.reply_text("❌ Gagal ambil harga")

    await update.message.reply_text(signal(price))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 BTC Bot aktif\n\n"
        "Command:\n"
        "/signal = ambil signal manual"
    )

# ================= POST INIT =================
async def post_init(app):
    asyncio.create_task(loop(app))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", send_signal))

    app.post_init = post_init

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
