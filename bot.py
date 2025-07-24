import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import gspread

# 🔐 Google Sheets credentials setup
gc = gspread.service_account(filename='credentials.json')
sh = gc.open("ssResellerOrders")
worksheet = sh.sheet1

# 📌 Enable logging
logging.basicConfig(level=logging.INFO)

# 🧠 User step tracking
user_data = {}

# ✅ START command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Place Order", callback_data='place_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("স্বাগতম! নিচের অপশনগুলো থেকে নির্বাচন করুন 👇", reply_markup=reply_markup)

# 📦 Start new order on button press
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data[user_id] = {
        "step": "customer_name",
        "order": {"username": query.from_user.username}
    }
    await query.message.reply_text("👤 কাস্টোমারের নাম লিখুন:")

# 📝 Handle all order inputs
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data:
        await update.message.reply_text("অনুগ্রহ করে নতুন করে অর্ডার দিতে '✅ Place Order' বাটনে ক্লিক করুন।")
        return

    text = update.message.text
    step = user_data[user_id]["step"]
    order = user_data[user_id]["order"]

    # ⛳ Step-by-step data collection
    if step == "customer_name":
        order["customers name"] = text
        user_data[user_id]["step"] = "phone"
        await update.message.reply_text("📞 কাস্টোমারের ফোন নাম্বার লিখুন:")
    elif step == "phone":
        order["customers phone"] = text
        user_data[user_id]["step"] = "address"
        await update.message.reply_text("📍 কাস্টোমারের ঠিকানা লিখুন:")
    elif step == "address":
        order["Address"] = text
        user_data[user_id]["step"] = "product"
        await update.message.reply_text("📦 প্রোডাক্টের নাম লিখুন:")
    elif step == "product":
        order["product name"] = text
        user_data[user_id]["step"] = "quantity"
        await update.message.reply_text("🔢 কুয়ান্টিটি লিখুন:")
    elif step == "quantity":
        order["quantity"] = text
        user_data[user_id]["step"] = "note"
        await update.message.reply_text("📝 যদি কিছু নোট থাকে, লিখুন (না থাকলে 'none' লিখুন):")
    elif step == "note":
        order["Note"] = text
        order["status"] = "Pending"
        order["balance"] = ""

        # ✅ সব তথ্য নিলে এক্সেলে লিখে দাও
        worksheet.append_row([
            order.get("username", ""),
            order.get("product name", ""),
            order.get("quantity", ""),
            order.get("Note", ""),
            order.get("customers name", ""),
            order.get("customers phone", ""),
            order.get("Address", ""),
            order.get("status", ""),
            order.get("balance", "")
        ])

        await update.message.reply_text("✅ অর্ডার সফলভাবে গ্রহণ করা হয়েছে!")
        user_data.pop(user_id)

# 🚀 Run bot
if __name__ == '__main__':
    app = ApplicationBuilder().token("8155815123:AAGYaNvyV9wzvGZVf0WsDkW59Y97LH9P9P8").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot running...")
    app.run_polling()
