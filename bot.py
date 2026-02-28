import os
from flask import Flask, request
import requests
import sqlite3
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
FREE_CHANNEL = "@kintradingsignal"
VIP_CHANNEL = "@KINGTRADINGSIGNAL9373"
ADMIN_ID = "@crowntradingsignalbot"
# ==========================================
# ==========================================

# -------- DATABASE SETUP --------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
                telegram_id TEXT,
                expiry TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS trades(
                pair TEXT,
                direction TEXT,
                entry TEXT,
                time TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

# -------- TELEGRAM SEND --------
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# -------- SIGNAL WEBHOOK --------
@app.route('/signal', methods=['POST'])
def signal():
    data = request.json

    pair = data['pair']
    direction = data['direction']
    price = data['price']

    message = f"""
🚨 SIGNAL ALERT

Pair: {pair}
Direction: {direction}
Entry: {price}
Risk: 1%
"""

    send_message(FREE_CHANNEL, message)
    send_message(VIP_CHANNEL, message + "\nVIP Management Active.")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO trades VALUES (?, ?, ?, ?)",
              (pair, direction, price, str(datetime.now())))
    conn.commit()
    conn.close()

    return "OK"

# -------- PAYMENT WEBHOOK --------
@app.route('/payment', methods=['POST'])
def payment():
    data = request.json

    telegram_id = data['custom_fields']['telegram_id']
    expiry = datetime.now() + timedelta(days=30)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?)",
              (telegram_id, expiry.isoformat()))
    conn.commit()
    conn.close()

    send_message(telegram_id, "✅ VIP Activated for 30 Days.")

    return "OK"

# -------- USER COMMAND HANDLER --------
@app.route('/telegram', methods=['POST'])
def telegram():
    data = request.json

    if "message" in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '').lower()

        if "/start" in text:
            send_message(chat_id, "Welcome to our Signal Service.\nType /price to see VIP plan.")

        elif "/price" in text:
            send_message(chat_id, "VIP Membership: $5/month.\nVisit our Gumroad link.")

        elif "/help" in text:
            send_message(chat_id, "Contact admin for support.")

    return "OK", 200


# -------- AUTO EXPIRY CHECK --------
def check_expiry():
    while True:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT telegram_id, expiry FROM users")
        users = c.fetchall()

        for user in users:
            if datetime.now() > datetime.fromisoformat(user[1]):
                requests.post(f"https://api.telegram.org/bot{TOKEN}/banChatMember",
                              data={"chat_id": VIP_CHANNEL,
                                    "user_id": user[0]})
                c.execute("DELETE FROM users WHERE telegram_id=?", (user[0],))

        conn.commit()
        conn.close()

        time.sleep(86400)

threading.Thread(target=check_expiry, daemon=True).start()

# -------- WEEKLY REPORT --------
def weekly_report():
    while True:
        time.sleep(604800)
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM trades")
        total = c.fetchone()[0]
        conn.close()

        send_message(VIP_CHANNEL, f"📊 Weekly Report\nTotal Signals Sent: {total}")

threading.Thread(target=weekly_report, daemon=True).start()


