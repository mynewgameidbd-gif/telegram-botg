import telebot
from telebot import types
import sqlite3
import datetime

TOKEN = "8969451047:AAGtqBKv9jDNtEyFQJAQUwlJZBg2K9cqdPY"
ADMIN_ID = 8742029952
bot = telebot.TeleBot(TOKEN)

def get_db():
    return sqlite3.connect('bot_database.db', check_same_thread=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📁 ফাইল সাবমিট")
    btn2 = types.KeyboardButton("💵 ব্যালেন্স")
    btn3 = types.KeyboardButton("🛠 সাপোর্ট")
    btn4 = types.KeyboardButton("💸 উইথড্র")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.reply_to(message, "স্বাগতম! আপনার প্রয়োজনীয় অপশনটি নিচে থেকে সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    if text == "📁 ফাইল সাবমিট":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Facebook Cookies", callback_data="sub_fb_cookies"),
            types.InlineKeyboardButton("Instagram 2FA", callback_data="sub_insta_2fa")
        )
        bot.send_message(user_id, "অনুগ্রহ করে আপনার ক্যাটাগরি সিলেক্ট করুন:", reply_markup=markup)
        
    elif text == "💵 ব্যালেন্স":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance, pending_withdraw, pending_work, total_income, completed_tasks, review_tasks FROM users WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        conn.close()
        
        if data:
            bal, p_with, p_work, tot_inc, comp, rev = data
            msg = f"""💵 **আপনার ব্যালেন্স**
━━━━━━━━━━━━━━━━━━━━━━
💵 ব্যালেন্স: {bal} BDT 
💸 পেন্ডিং (উইথড্র): {p_with:.2f} BDT
⏳ কাজের পেন্ডিং টাকা: {p_work:.2f} BDT
💰 মোট ইনকাম: {tot_inc:.2f} BDT
━━━━━━━━━━━━━━━━━━━━━━
✔️ সম্পন্ন কাজ: {comp} টি
⏳ রিভিউতে আছে: {rev} টি"""
            bot.send_message(user_id, msg, parse_mode="Markdown")
            
    elif text == "🛠 সাপোর্ট":
        bot.send_message(user_id, f"যেকোনো সমস্যায় সরাসরি যোগাযোগ করুন: @YourAdminUsername\nএডমিন আইডি: `{ADMIN_ID}`", parse_mode="Markdown")
        
    elif text == "💸 উইথড্র":
        msg = bot.send_message(user_id, "আপনার পেমেন্ট মেথড সিলেক্ট করুন (বিকাশ / নগদ / বাইন্যান্স):")
        bot.register_next_step_handler(msg, process_withdraw_method)

def process_withdraw_method(message):
    method = message.text
    msg = bot.send_message(message.chat.id, f"আপনি {method} সিলেক্ট করেছেন। আপনার একাউন্ট নম্বর অথবা বাইন্যান্স UID দিন এবং সাথে অ্যামাউন্ট লিখুন:")
    bot.register_next_step_handler(msg, lambda m: save_withdraw_request(m, method))

def save_withdraw_request(message, method):
    user_id = message.from_user.id
    details = message.text
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    
    if res and res[0] >= 50:  # সর্বনিম্ন উইথড্র লিমিট (যেমন 50 টাকা)
        cursor.execute("INSERT INTO withdraws (user_id, amount, method, account_info) VALUES (?, ?, ?, ?)", (user_id, res[0], method, details))
        cursor.execute("UPDATE users SET balance = 0, pending_withdraw = pending_withdraw + ? WHERE user_id = ?", (res[0], user_id))
        conn.commit()
        bot.send_message(user_id, "✅ উইথড্র রিকোয়েস্ট সফলভাবে পাঠানো হয়েছে! কিছুক্ষণের মধ্যে পেমেন্ট পেয়ে যাবেন।")
        bot.send_message(ADMIN_ID, f"🔔 নতুন উইথড্র রিকোয়েস্ট এসেছে!\nইউজার আইডি: `{user_id}`\nমেথড: {method}\nডিটেইলস: {details}", parse_mode="Markdown")
    else:
        bot.send_message(user_id, "⚠️ আপনার পর্যাপ্ত ব্যালেন্স নেই অথবা সর্বনিম্ন উইথড্র লিমিটের নিচে রয়েছে।")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def callback_submission(call):
    category = "Facebook Cookies" if call.data == "sub_fb_cookies" else "Instagram 2FA"
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    
    format_guide = "A. Uid\nB. Password\nC. Cookies" if "cookies" in call.data else "A. Username\nB. Password\nC. 2fa"
    
    msg = f"""📱 **{category} সাবমিট**
📅 ডেট: {today_date}

➡️ অনুগ্রহ করে আপনার .xlsx ফাইলটি আপলোড করুন, যেখানে ফরম্যাট হবে:
{format_guide}"""
    
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: handle_excel_file(m, category))

def handle_excel_file(message, category):
    if message.document:
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        file_name = message.document.file_name
        
        # ডাটাবেসে পেন্ডিং হিসেবে সেভ করা
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO submissions (user_id, username, category, total_ids, status, date) VALUES (?, ?, ?, ?, ?, ?)", 
                       (user_id, username, category, 10, 'Pending', datetime.date.today().strftime("%Y-%m-%d")))
        cursor.execute("UPDATE users SET review_tasks = review_tasks + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ ফাইল রিসিভ করা হয়েছে!\n📁 ফাইলের নাম: {file_name}\n📂 আপনার ফাইলটি পেন্ডিং রিভিউতে চলে গেছে।")
        
        # এডমিন বটে ফাইল ও নোটিফিকেশন ফরওয়ার্ড করা
        bot.send_message(ADMIN_ID, f"📥 নতুন ফাইল সাবমিশন!\n👤 ইউজার: @{username} (`{user_id}`)\n📂 ক্যাটাগরি: {category}", parse_mode="Markdown")
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    else:
        bot.reply_to(message, "⚠️ অনুগ্রহ করে একটি সঠিক `.xlsx` ফাইল পাঠান।")

if __name__ == '__main__':
    print("User Bot is running...")
    bot.polling(none_stop=True)
