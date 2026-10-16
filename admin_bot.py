import telebot
from telebot import types
import sqlite3

ADMIN_TOKEN = "8947059922:AAHHJlU8FrzE86RKm8M4pJ5yP4wCXUcqrLc"
ADMIN_ID = 8742029952
bot = telebot.TeleBot(ADMIN_TOKEN)

@bot.message_handler(commands=['start'])
def admin_start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⚠️ আপনি এই বটের এডমিন নন!")
        return
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📢 ব্রডকাস্ট মেসেজ"),
        types.KeyboardButton("📊 পেন্ডিং সাবমিশন চেক"),
        types.KeyboardButton("💰 উইথড্র রিকোয়েস্ট")
    )
    bot.reply_to(message, "স্বাগতম বস! এটি আপনার এডমিন প্যানেল।", reply_markup=markup)

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "📢 ব্রডকাস্ট মেসেজ")
def broadcast_prompt(message):
    msg = bot.reply_to(message, "সব ইউজারের কাছে যে মেসেজটি পাঠাতে চান সেটি লিখুন:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], f"📢 **অফিসিয়াল নোটিশ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except:
            pass
            
    bot.send_message(ADMIN_ID, f"সফলভাবে {count} জন ইউজারের কাছে ব্রডকাস্ট মেসেজ পাঠানো হয়েছে।")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text == "💰 উইথড্র রিকোয়েস্ট")
def check_withdraws(message):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, amount, method, account_info FROM withdraws WHERE status = 'Pending'")
    withdraws = cursor.fetchall()
    conn.close()
    
    if not withdraws:
        bot.reply_to(message, "কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই।")
        return
        
    for w in withdraws:
        w_id, u_id, amt, method, info = w
        msg = f"""💸 **উইথড্র রিকোয়েস্ট ID: {w_id}**
👤 ইউজার আইডি: `{u_id}`
💵 পরিমাণ: {amt} BDT
📱 মেথড: {method}
ℹ️ একাউন্ট তথ্য: {info}"""
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{w_id}_{u_id}_{amt}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{w_id}_{u_id}_{amt}")
        )
        bot.send_message(ADMIN_ID, msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_") or call.data.startswith("rej_"))
def handle_withdraw_action(call):
    data = call.data.split("_")
    action = data[0]
    w_id = data[1]
    u_id = data[2]
    amt = float(data[3])
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    if action == "app":
        cursor.execute("UPDATE withdraws SET status = 'Approved' WHERE id = ?", (w_id,))
        cursor.execute("UPDATE users SET pending_withdraw = pending_withdraw - ?, total_income = total_income + ?, completed_tasks = completed_tasks + 1 WHERE user_id = ?", (amt, amt, u_id))
        conn.commit()
        bot.send_message(int(u_id), f"🎉 আপনার উইথড্র রিকোয়েস্ট এপ্রুভ হয়েছে! {amt} BDT পেমেন্ট সম্পন্ন করা হয়েছে।")
        bot.edit_message_text(f"✅ উইথড্র ID {w_id} এপ্রুভ করা হয়েছে।", call.message.chat.id, call.message.message_id)
    else:
        cursor.execute("UPDATE withdraws SET status = 'Rejected' WHERE id = ?", (w_id,))
        cursor.execute("UPDATE users SET balance = balance + ?, pending_withdraw = pending_withdraw - ? WHERE user_id = ?", (amt, amt, u_id))
        conn.commit()
        bot.send_message(int(u_id), f"❌ আপনার উইথড্র রিকোয়েস্ট রিজেক্ট করা হয়েছে। আপনার টাকা ব্যালেন্সে ফেরত দেওয়া হয়েছে।")
        bot.edit_message_text(f"❌ উইথড্র ID {w_id} রিজেক্ট করা হয়েছে।", call.message.chat.id, call.message.message_id)
        
    conn.close()

if __name__ == '__main__':
    print("Admin Bot is running...")
    bot.polling(none_stop=True)
