import os
import asyncio
import requests
from datetime import datetime, timedelta
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =====================
# ENV
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID missing")

CHAT_ID = int(CHAT_ID)

# =====================
# CONFIG
# =====================
SYMBOL = "BTCUSDT"
TZ = pytz.timezone("Asia/Jakarta")

TP1_PIPS = 100
TP2_PIPS = 150
SL_PIPS  = 50

# =====================
# PRICE (BINANCE)
# =====================
def get_price():
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        r = requests.get(url, timeout=10)
        return float(r.json()["price"])
    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# =====================
# SIGNAL
# =====================
import random

def generate_signal(price):
    direction = random.choice(["BUY", "SELL"])

    if direction == "BUY":
        tp1 = price + TP1_PIPS
        tp2 = price + TP2_PIPS
        sl  = price - SL_PIPS
    else:
        tp1 = price - TP1_PIPS
        tp2 = price - TP2_PIPS
        sl  = price + SL_PIPS

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    return f"""
📊 BTCUSDT SIGNAL

🕒 {now}
💰 Price: {price}

📈 Direction: {direction}

🎯 TP1: {tp1:.2f}
🎯 TP2: {tp2:.2f}
⛔ SL : {sl:.2f}

━━━━━━━━━━━━━━
⚠️ Risk Management Wajib
"""

# =====================
# LOOP (EVERY :30)
# =====================
async def scheduler(app):
    print("🚀 Scheduler started")

    while True:
        now = datetime.now(TZ)

        next_run = now.replace(minute=30, second=0, microsecond=0)

        if now.minute >= 30:
            next_run = (now + timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)

        wait = (next_run - now).total_seconds()
        await asyncio.sleep(wait)

        price = get_price()
        if not price:
            continue

        msg = generate_signal(price)

        try:
            await app.bot.send_message(chat_id=CHAT_ID, text=msg)
            print("✅ Signal sent")
        except Exception as e:
            print("SEND ERROR:", e)

# =====================
# COMMAND
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 BTCUSDT Bot aktif (setiap jam :30)")

# =====================
# POST INIT
# =====================
async def post_init(app):
    asyncio.create_task(scheduler(app))

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.post_init = post_init

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
