import telebot
from telebot import types
import sqlite3
import datetime
import requests
import os
import time

# --- CONFIGURATION ---
API_TOKEN = '8679668152:AAEpAbyM_LhbOMsqRgcQdpJw_kpCnkMnwpQ'
ADMIN_ID = 8339811190
ELEVENLABS_KEY = 'sk_7e27f8b3c72b1901e537ccb5067781aa049c64767d36a29d'.strip()
CHANNEL_LINK = "https://t.me/shushi_ai_official"

# --- UPDATED LIMITS AS PER YOUR REQUEST ---
LIMITS = {1: 20, 7: 100, 30: 350}

bot = telebot.TeleBot(API_TOKEN)

def init_db():
    conn = sqlite3.connect('shushi_pro_original.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, expiry TEXT, selected_plan INTEGER, 
                  used_count INTEGER DEFAULT 0, total_limit INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_available_voice():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": ELEVENLABS_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            voices = response.json().get('voices', [])
            if voices: return voices[0]['voice_id']
    except: pass
    return None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn_subscribe = types.InlineKeyboardButton("📢 Subscribe Channel", url=CHANNEL_LINK)
    btn_agree = types.InlineKeyboardButton("✅ I Agree", callback_data="agree")
    markup.add(btn_subscribe)
    markup.add(btn_agree)
    bot.send_photo(message.chat.id, 'AgACAgUAAxkBAAID3WnUc6mdxNTt32EVzNZnogoU7PPtAAKgDmsbB3mhViL-_CXCG7EWAQADAgADeAADOwQ', caption="🌟 **Welcome to Shushi AI!**\n\nConvert voices to Indian Girl voice. Choose a plan to start!", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    try:
        if call.data == "agree":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔊 Check Demo on Channel", url=CHANNEL_LINK))
            markup.add(types.InlineKeyboardButton("💎 Choose Plan", callback_data="show_plans"))
            bot.send_photo(call.message.chat.id, 'AgACAgUAAxkBAAID5GnUdT6JV-YEpqiCLEMOSWVvb8KLAAKjDmsbB3mhVvZy4jWJ3LeHAQADAgADeAADOwQ', caption="Premium plan lene ke liye niche button dabayein! 😍", reply_markup=markup)
        
        elif call.data == "show_plans":
            markup = types.InlineKeyboardMarkup()
            # --- UPDATED PLAN BUTTONS ---
            markup.add(types.InlineKeyboardButton(f"⚡ 1 Day (20 Voices) - ₹30", callback_data="plan_1"))
            markup.add(types.InlineKeyboardButton(f"💎 1 Week (100 Voices) - ₹150", callback_data="plan_7"))
            markup.add(types.InlineKeyboardButton(f"🔥 1 Month (350 Voices) - ₹700", callback_data="plan_30"))
            bot.send_message(call.message.chat.id, "👑 **Premium Plans**\nSelect your plan to get Payment QR:", reply_markup=markup)
        
        elif call.data.startswith("plan_"):
            days = int(call.data.split("_")[1])
            conn = sqlite3.connect('shushi_pro_original.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO users (user_id, selected_plan, used_count, total_limit) VALUES (?, ?, 0, 0)", (user_id, days))
            conn.commit()
            conn.close()
            qr_map = {1: 'AgACAgUAAxkBAAMEadDd39cuX1OyBFAJUpLjt3N4fUoAAq4Oaxuf9IlWWtbv1akAAVSUAQADAgADeQADOwQ', 7: 'AgACAgUAAxkBAAMFadDd--nSZq61MqUKllvu1Y4c_JoAArEOaxuf9IlWtzGR3YpHzXYBAAMCAAN5AAM7BA', 30: 'AgACAgUAAxkBAAMGadDeEEXHbE5HmVpu-mDo5l9nQL0AArMOaxuf9IlWprNA-dcQZpcBAAMCAAN5AAM7BA'}
            bot.send_photo(call.message.chat.id, qr_map[days], caption=f"✅ Plan Selected: {LIMITS[days]} Voices.\n\nIS QR PAR PAY KAREIN AUR SCREENSHOT BHEJEIN.")
        
        elif call.data.startswith("approve_"):
            uid = int(call.data.split("_")[1])
            conn = sqlite3.connect('shushi_pro_original.db')
            c = conn.cursor()
            c.execute("SELECT selected_plan FROM users WHERE user_id=?", (uid,))
            res = c.fetchone()
            days = res[0] if (res and res[0]) else 1
            # --- UPDATED APPROVAL LIMITS ---
            limit = LIMITS.get(days, 20)
            expiry_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            c.execute("UPDATE users SET expiry=?, used_count=0, total_limit=?, selected_plan=NULL WHERE user_id=?", (expiry_date, limit, uid))
            conn.commit()
            conn.close()
            bot.send_message(uid, f"🎉 Payment Success! Access Granted.\nTotal Voices: {limit}\nValid till: {expiry_date}")
            bot.edit_message_caption(f"✅ Approved {uid} for {limit} voices", call.message.chat.id, call.message.message_id)
            
    except Exception as e: print(f"Error: {e}")

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    if message.caption and any(word in message.caption for word in ["Welcome", "Premium", "Selected"]): return 
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve ✅", callback_data=f"approve_{message.from_user.id}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💰 Screenshot from {message.from_user.id}", reply_markup=markup)
    bot.reply_to(message, "⏳ Wait karein, admin check kar raha hai...")

@bot.message_handler(content_types=['voice'])
def voice_engine(message):
    user_id = message.from_user.id
    if message.voice.duration > 20:
        bot.reply_to(message, "❌ Voice bahut badi hai! Max 20 seconds allowed.")
        return

    conn = sqlite3.connect('shushi_pro_original.db')
    c = conn.cursor()
    c.execute("SELECT expiry, used_count, total_limit FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if row is None or row[0] is None:
        bot.reply_to(message, "❌ Voice convert karne ke liye pehle ek premium plan choose karein! /start dabayein.")
        conn.close()
        return

    expiry_time = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.now() < expiry_time and row[1] < row[2]:
        bot.reply_to(message, f"🔄 Converting... ({row[1] + 1}/{row[2]})")
        try:
            voice_id = get_available_voice()
            file_info = bot.get_file(message.voice.file_id)
            audio_data = bot.download_file(file_info.file_path)
            res = requests.post(f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}", headers={"xi-api-key": ELEVENLABS_KEY}, files={"audio": ("v.ogg", audio_data, "audio/ogg")}, data={"model_id": "eleven_multilingual_sts_v2"})
            if res.status_code == 200:
                c.execute("UPDATE users SET used_count = used_count + 1 WHERE user_id=?", (user_id,))
                conn.commit()
                file_name = f"Voice_{user_id}.mp3"
                with open(file_name, 'wb') as f: f.write(res.content)
                with open(file_name, 'rb') as audio:
                    bot.send_audio(message.chat.id, audio, caption="✨ Shushi AI Result")
                os.remove(file_name)
        except: pass
    else:
        bot.reply_to(message, "❌ Plan Expired ya Limit khatam! Naya plan khareedein.")
    conn.close()

if __name__ == "__main__":
    init_db()
    while True:
        try: bot.infinity_polling(timeout=20)
        except: time.sleep(5)
