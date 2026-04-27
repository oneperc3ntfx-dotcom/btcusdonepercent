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
# ENV SAFE LOAD
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")

if not CHAT_ID:
    raise ValueError("❌ CHAT_ID missing")

CHAT_ID = int(CHAT_ID)

# =========================
# CONFIG
# =========================

TZ = pytz.timezone("Asia/Jakarta")

# =========================
# PRICE (BINANCE)
# =========================

def get_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
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
        tp1 = price + 100
        tp2 = price + 150
        sl  = price - 50
    else:
        tp1 = price - 100
        tp2 = price - 150
        sl  = price + 50

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

📌 Market Outlook:
Hindari entry saat harga tidak sesuai market structure,
hindari candle agresif, dan hindari news high impact.

⚠️ Risk Management wajib digunakan.
"""

# =========================
# SCHEDULER (:30 EVERY HOUR)
# =========================

async def scheduler(app):

    while True:
        try:
            now = datetime.now(TZ)

            next_run = now.replace(minute=30, second=0, microsecond=0)

            if now.minute >= 30:
                next_run = (now + timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)

            wait = (next_run - now).total_seconds()

            print(f"⏳ Waiting {int(wait)} seconds for next signal")

            await asyncio.sleep(wait)

            price = get_price()
            if not price:
                continue

            msg = generate_signal(price)

            await app.bot.send_message(chat_id=CHAT_ID, text=msg)

            print("✅ Signal sent")

        except Exception as e:
            print("SCHEDULER ERROR:", e)
            await asyncio.sleep(5)

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 BTCUSD Bot Active (24/7 :30 schedule)")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    price = get_price()
    if not price:
        return await update.message.reply_text("No price")

    await update.message.reply_text(generate_signal(price))

# =========================
# POST INIT
# =========================

async def post_init(app):
    asyncio.create_task(scheduler(app))
    print("🚀 Scheduler started")

# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    app.post_init = post_init

    print("🤖 Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
