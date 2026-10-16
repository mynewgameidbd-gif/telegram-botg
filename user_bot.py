import telebot
from telebot import types
import sqlite3
import datetime
import openpyxl
import os

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
    
    bot.reply_to(message, "✨ **স্বাগতম!** আপনার প্রয়োজনীয় সার্ভিসটি নিচ থেকে সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    user_id = message.from_user.id
    
    if text == "📁 ফাইল সাবমিট":
        # এডমিন থেকে সার্ভিস অন আছে কিনা চেক করার অপশন
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📱 Facebook Cookies", callback_data="sub_fb_cookies"),
            types.InlineKeyboardButton("📸 Instagram 2FA", callback_data="sub_insta_2fa")
        )
        bot.send_message(user_id, "📂 **ফাইল সাবমিট করার ক্যাটাগরি সিলেক্ট করুন:**", parse_mode="Markdown", reply_markup=markup)
        
    elif text == "💵 ব্যালেন্স":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance, pending_withdraw, pending_work, total_income, completed_tasks, review_tasks FROM users WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        
        # ইউজারের সাবমিট করা মোট পেন্ডিং আইডি সংখ্যা বের করা
        cursor.execute("SELECT SUM(total_ids) FROM submissions WHERE user_id = ? AND status = 'Pending'", (user_id,))
        pending_ids_sum = cursor.fetchone()[0] or 0
        conn.close()
        
        if data:
            bal, p_with, p_work, tot_inc, comp, rev = data
            msg = f"""💵 **আপনার একাউন্ট ব্যালেন্স**
━━━━━━━━━━━━━━━━━━━━━━
💰 মূল ব্যালেন্স: `{bal:.2f} BDT` 
💸 পেন্ডিং উইথড্র: `{p_with:.2f} BDT`
⏳ কাজের পেন্ডিং টাকা: `{p_work:.2f} BDT`
📈 মোট ইনকাম: `{tot_inc:.2f} BDT`
━━━━━━━━━━━━━━━━━━━━━━
✔️ সম্পন্ন কাজ: `{comp}` টি
⏳ রিভিউতে থাকা আইডি: `{pending_ids_sum}` টি"""
            bot.send_message(user_id, msg, parse_mode="Markdown")
            
    elif text == "🛠 সাপোর্ট":
        bot.send_message(user_id, "🛠 **সাপোর্ট সেন্টার**\n\nযেকোনো সমস্যায় সরাসরি এডমিনের সাথে যোগাযোগ করুন:\n👉 @YourAdminUsername", parse_mode="Markdown")
        
    elif text == "💸 উইথড্র":
        msg = bot.send_message(user_id, "💸 পেমেন্ট নেওয়ার জন্য আপনার মাধ্যমটি সিলেক্ট করুন:\n(যেমন: `বিকাশ`, `নগদ` অথবা `বাইনান্স`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_withdraw_method)

def process_withdraw_method(message):
    method = message.text
    msg = bot.send_message(message.chat.id, f"✅ আপনি **{method}** সিলেক্ট করেছেন।\n\nএখন আপনার বিকাশ/নগদ নম্বর অথবা বাইন্যান্স UID এবং সাথে কত টাকা উইথড্র করতে চান তা লিখে পাঠান:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: save_withdraw_request(m, method))

def save_withdraw_request(message, method):
    user_id = message.from_user.id
    details = message.text
    
    conn = get_db()
    cursor = conn.cursor()
    # ডাটাবেস থেকে সর্বনিম্ন উইথড্র লিমিট চেক করা (ডিফল্ট ৫০ টাকা)
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    
    if res and res[0] >= 50:
        amt = res[0]
        cursor.execute("INSERT INTO withdraws (user_id, amount, method, account_info) VALUES (?, ?, ?, ?)", (user_id, amt, method, details))
        cursor.execute("UPDATE users SET balance = 0, pending_withdraw = pending_withdraw + ? WHERE user_id = ?", (amt, user_id))
        conn.commit()
        bot.send_message(user_id, "🎉 **উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!**\nখুব শীঘ্রই আপনার পেমেন্ট কমপ্লিট করা হবে।", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n👤 ইউজার আইডি: `{user_id}`\n💵 পরিমাণ: `{amt} BDT`\n📱 মেথড: `{method}`\n📝 তথ্য: `{details}`", parse_mode="Markdown")
    else:
        bot.send_message(user_id, "⚠️ আপনার পর্যাপ্ত ব্যালেন্স নেই অথবা সর্বনিম্ন উইথড্র সীমার নিচে রয়েছে।")
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def callback_submission(call):
    category = "Facebook Cookies" if call.data == "sub_fb_cookies" else "Instagram 2FA"
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    
    format_guide = "A. Uid\nB. Password\nC. Cookies" if "cookies" in call.data else "A. Username\nB. Password\nC. 2fa"
    
    msg = f"""📱 **{category} সাবমিট**
📅 ডেট: `{today_date}`

➡️ অনুগ্রহ করে আপনার `.xlsx` ফাইলটি আপলোড করুন, যেখানে ফরম্যাট থাকবে:
{format_guide}"""
    
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: handle_excel_file(m, category))

def handle_excel_file(message, category):
    if message.document and message.document.file_name.endswith('.xlsx'):
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # লোকালভাবে ফাইল সেভ করে এক্সেল কাউন্ট করা
        local_filename = f"sub_{user_id}.xlsx"
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        try:
            wb = openpyxl.load_workbook(local_filename)
            sheet = wb.active
            total_ids = sheet.max_row - 1 # হেডার বাদ দিয়ে রো গণনা
            if total_ids < 1:
                total_ids = sheet.max_row
        except:
            total_ids = 0
            
        if os.path.exists(local_filename):
            os.remove(local_filename)
            
        # ডাটাবেসে সেভ করা
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO submissions (user_id, username, category, total_ids, status, date) VALUES (?, ?, ?, ?, ?, ?)", 
                       (user_id, username, category, total_ids, 'Pending', datetime.date.today().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        
        # ইউজারকে প্রফেশনাল কনফার্মেশন মেসেজ
        bot.reply_to(message, f"✅ **ফাইল সফলভাবে রিসিভ করা হয়েছে!**\n\n📊 ফাইলের আইডি সংখ্যা: `{total_ids}` টি\n⏳ আপনার আইডিগুলো পেন্ডিং রিভিউতে চলে গেছে।", parse_mode="Markdown")
        
        # সরাসরি এডমিন বটে ফাইল ও নোটিফিকেশন পাঠানো
        admin_caption = f"📥 **নতুন ফাইল সাবমিশন!**\n\n👤 ইউজার: @{username} (`{user_id}`)\n📂 ক্যাটাগরি: `{category}`\n📊 মোট আইডি: `{total_ids}` টি"
        bot.send_document(ADMIN_ID, message.document.file_id, caption=admin_caption, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ অনুগ্রহ করে একটি সঠিক `.xlsx` ফরম্যাটের এক্সেল ফাইল পাঠান।")

if __name__ == '__main__':
    print("User Bot is running professionally...")
    bot.polling(none_stop=True)
