#!/usr/bin/env python3

import os
import asyncio
import random
from datetime import datetime, timedelta

import pytz
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# ENV
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN or CHAT_ID missing")

# =========================
# CONFIG
# =========================

SYMBOL = "BTCUSDT"
TZ = pytz.timezone("Asia/Jakarta")

PIP = 1  # BTC scaling

# =========================
# PRICE SOURCE (BINANCE)
# =========================

def get_price():
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        res = requests.get(url, timeout=10)
        return float(res.json()["price"])
    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# =========================
# SIGNAL ENGINE
# =========================

def generate_signal(price: float):

    direction = random.choice(["BUY", "SELL"])

    if direction == "BUY":
        tp1 = price + 100 * PIP
        tp2 = price + 150 * PIP
        sl  = price - 50 * PIP
    else:
        tp1 = price - 100 * PIP
        tp2 = price - 150 * PIP
        sl  = price + 50 * PIP

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    return f"""
📊 BTCUSD SIGNAL

🕒 Time : {now}
💰 Price : {price}

📈 Direction : {direction}

🎯 TP1 : {round(tp1,2)}
🎯 TP2 : {round(tp2,2)}
⛔ SL  : {round(sl,2)}

━━━━━━━━━━━━━━━━━━

📌 Outlook:
BTCUSD menunjukkan volatilitas tinggi dengan peluang intraday di kedua arah.

⚠️ Risk Warning:
- Hindari entry saat market tidak jelas
- Hindari candle agresif (spike tinggi)
- Gunakan konfirmasi tambahan sebelum entry
"""

# =========================
# SCHEDULER (:30 EVERY HOUR)
# =========================

async def scheduler(app):

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
            await app.bot.send_message(
                chat_id=CHAT_ID,
                text=msg
            )
            print("✅ Signal sent")
        except Exception as e:
            print("SEND ERROR:", e)

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 BTCUSD Signal Bot Active (24/7 :30 scheduler)")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = get_price()
    if not price:
        return await update.message.reply_text("No price available")

    await update.message.reply_text(generate_signal(price))

# =========================
# POST INIT
# =========================

async def post_init(app):
    asyncio.create_task(scheduler(app))
    print("🚀 Scheduler started (:30 mode)")

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    app.post_init = post_init

    print("🤖 Bot Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
