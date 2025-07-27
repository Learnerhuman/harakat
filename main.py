import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters,
                          ConversationHandler, CallbackQueryHandler, ContextTypes)
import os
from dotenv import load_dotenv

load_dotenv()
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_ID=6238734044
# Fayl nomi
DATA_FILE = 'users.json'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Yo'nalishlar
DIRECTIONS = ["Iqtisodiyot", "Soliq", "Moliya", "Menejment", "Bank ishi", "Jahon iqtisodiyoti"]




# Bosqichlar
(REGISTER_PHONE, REGISTER_NAME, SELECT_DIRECTION, ENTER_SCORE,
 EDIT_FIELD_SELECT, EDIT_VALUE_INPUT) = range(6)

# Ma'lumotlarni yuklash

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

# Ma'lumotlarni saqlash

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id in data:
        await update.message.reply_text("Siz allaqachon ro'yhatdan o'tgansiz.\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit")
    else:
        await update.message.reply_text("Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Telefon raqamni yuborish", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True))
        return REGISTER_PHONE

# Telefon raqamni qabul qilish
async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Iltimos, 'Telefon raqamni yuborish' tugmasini bosing.")
        return REGISTER_PHONE

    user_id = str(update.effective_user.id)
    context.user_data['phone'] = contact.phone_number
    await update.message.reply_text("Ismingiz va familiyangizni kiriting:")
    return REGISTER_NAME

# Ism familiya
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    keyboard = [[InlineKeyboardButton(d, callback_data=d)] for d in DIRECTIONS]
    await update.message.reply_text("Yo'nalishni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_DIRECTION

# Yo'nalish tanlash
async def select_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['direction'] = query.data
    await query.edit_message_text("Endi o'z ballingizni kiriting (56-100 oralig'ida):")
    return ENTER_SCORE

# Ball kiritish
async def enter_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = float(update.message.text)
        if not (56 <= score <= 100):
            raise ValueError
    except:
        await update.message.reply_text("Noto'g'ri ball. 56 dan 100 gacha son kiriting.")
        return ENTER_SCORE

    user_id = str(update.effective_user.id)
    data = load_data()
    data[user_id] = {
        "phone": context.user_data['phone'],
        "full_name": context.user_data['full_name'],
        "direction": context.user_data['direction'],
        "score": score
    }
    save_data(data)
    await update.message.reply_text("Ma'lumotlaringiz saqlandi!\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit")
    return ConversationHandler.END

# /reyting
async def reyting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    keyboard = [[InlineKeyboardButton(d, callback_data=f"r:{d}")] for d in DIRECTIONS]
    await update.message.reply_text("Qaysi yo'nalish bo'yicha reytingni ko'rmoqchisiz?",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# Reyting tanlash
async def reyting_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction = query.data.split(":")[1]
    data = load_data()
    filtered = [(v['full_name'], v['score']) for v in data.values() if v['direction'] == direction]
    sorted_data = sorted(filtered, key=lambda x: x[1], reverse=True)
    text = f"📊 <b>{direction}</b> yo'nalishi reytingi:\n"
    for i, (name, score) in enumerate(sorted_data, 1):
        text += f"{i}. {name} - {score}\n"
    await query.edit_message_text(text+"\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit", parse_mode='HTML')

# /edit
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("Siz ro'yhatdan o'tmagansiz.\nRo'yhatdan o'tish uchun /start")
        return
    keyboard = [
        [InlineKeyboardButton("Ism", callback_data="field:full_name")],
        [InlineKeyboardButton("Yo'nalish", callback_data="field:direction")],
        [InlineKeyboardButton("Ball", callback_data="field:score")]
    ]
    await update.message.reply_text("Qaysi ma'lumotni o'zgartirmoqchisiz?",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_FIELD_SELECT

# Maydon tanlash
async def edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.split(":")[1]
    context.user_data['edit_field'] = field
    if field == "direction":
        keyboard = [[InlineKeyboardButton(d, callback_data=f"dir:{d}")] for d in DIRECTIONS]
        await query.edit_message_text("Yangi yo'nalishni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_VALUE_INPUT
    await query.edit_message_text("Yangi qiymatni yuboring:")
    return EDIT_VALUE_INPUT

# Yangi qiymat
async def edit_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    field = context.user_data['edit_field']
    if update.callback_query:
        value = update.callback_query.data.split(":")[1]
        await update.callback_query.edit_message_text("O'zgartirildi.\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit")
    else:
        value = update.message.text
        await update.message.reply_text("O'zgartirildi.\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit")

    if field == "score":
        try:
            value = float(value)
            if not (56 <= value <= 100): raise ValueError
        except:
            await update.message.reply_text("Noto'g'ri ball. 56 dan 100 gacha son kiriting")
            return EDIT_VALUE_INPUT

    data[user_id][field] = value
    save_data(data)
    return ConversationHandler.END

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Faqat admin uchun.")
        return
    data = load_data()
    text = "👮 Admin panel:\n"
    for user_id, v in data.items():
        text += f"{v['full_name']} | {v['phone']} | {v['direction']} | {v['score']}\n"
    await update.message.reply_text(text+"\nReytinglarni ko'rish uchun /reyting\nMa'lumotni o'zgartirish uchun /edit")

# Asosiy
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER_PHONE: [MessageHandler(filters.CONTACT, register_phone)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            SELECT_DIRECTION: [CallbackQueryHandler(select_direction)],
            ENTER_SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_score)]
        },
        fallbacks=[]
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit)],
        states={
            EDIT_FIELD_SELECT: [CallbackQueryHandler(edit_field_select, pattern="^field:.*")],
            EDIT_VALUE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_input),
                               CallbackQueryHandler(edit_value_input, pattern="^dir:.*")]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(edit_conv)
    app.add_handler(CommandHandler("reyting", reyting))
    app.add_handler(CallbackQueryHandler(reyting_direction, pattern="^r:.*"))
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()
