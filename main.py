import os
import threading
from flask import Flask
from telebot import TeleBot, types
from openai import OpenAI

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

# Your Social Links
CHANNEL_ID = -1006687974478
CHANNEL_URL = "https://t.me/silkroad105"
INSTA_URL = "https://www.instagram.com/arshux._?igsh=MXhndmhlMnY5Zm83bQ=="
YT_URL = "https://www.youtube.com/@silk_road402"

# --- INITIALIZE CLIENTS ---
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- WEB SERVER FOR RENDER ---
@app.route('/')
def index():
    return "Bot is running with Image Layout!"

# --- HELPER: CHECK MEMBERSHIP ---
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# --- UI: IMAGE STYLE BUTTONS ---
def get_start_markup():
    markup = types.InlineKeyboardMarkup()
    
    # Row 1: Two buttons side by side
    btn_channel = types.InlineKeyboardButton("📢 Channel", url=CHANNEL_URL)
    btn_updates = types.InlineKeyboardButton("🤖 Updates", url=YT_URL) # Using YT for updates
    
    # Row 2: One big button at the bottom
    btn_enter = types.InlineKeyboardButton("🚀 Enter WormGPT", callback_data="verify_and_start")
    
    # Adding to markup
    markup.row(btn_channel, btn_updates)
    markup.row(btn_enter)
    
    return markup

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    welcome_text = (
        f"Hello {message.from_user.first_name}! 👋\n\n"
        "To use **WormGPT AI**, you must join our channel first."
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text,
        reply_markup=get_start_markup(),
        parse_mode="Markdown"
    )

# --- CALLBACK HANDLER (The "Enter WormGPT" Button) ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_and_start")
def verify_user(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Access Granted!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ **Access Granted!**\n\nYou have entered WormGPT. How can I help you today?",
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(
            call.id, 
            "❌ Access Denied! Please join the channel first.", 
            show_alert=True
        )

# --- AI CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def chat_handler(message):
    # Check if user is a member
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "⚠️ **Subscription Required!**\n\nPlease join the channel to unlock WormGPT.",
            reply_markup=get_start_markup(),
            parse_mode="Markdown"
        )
        return

    # Process AI if they are a member
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        chat_completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[{"role": "user", "content": message.text}],
            max_tokens=800
        )

        reply = chat_completion.choices[0].message.content
        bot.reply_to(message, reply)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "❌ AI is currently offline. Try again later.")

# --- RUNNER ---
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
