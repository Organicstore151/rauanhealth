import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import ReplyKeyboardMarkup, KeyboardButton

# Google Sheets подключение
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.environ["SPREADSHEET_URL"]).sheet1

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("🌅 Утро")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Пиши данные за день (вода, питание и т.д.) или нажми кнопку 👇",
        reply_markup=reply_markup
    )
# Обработка обычных сообщений
async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "☀️ Доброе утро, Рауан!\n"
        "Вот 3 простых шага для запуска пищеварения и энергии:\n\n"
        "1. 💧 Выпей стакан тёплой воды (можно с лимоном)\n"
        "2. 🍽️ Завтрак — овсянка, гречка или яйца + овощи\n"
        "3. 🤸 Разминка 5 минут: наклоны, «велосипед» и лёгкие приседания\n\n"
        "Пусть день будет лёгким и продуктивным! 🔥"
    )
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "утро" in text or "morning" in text:
        await morning(update, context)
        return

    # иначе обрабатываем как обычный трекинг
    row = [""] * 11
    row[0] = datetime.now().strftime("%Y-%m-%d")
    for line in text.split('\n'):
        if "стул" in line:
            row[1] = line.split(":", 1)[-1].strip()
        elif "вода" in line:
            row[2] = line.split(":", 1)[-1].strip()
        elif "движение" in line:
            row[3] = line.split(":", 1)[-1].strip()
        elif "завтрак" in line:
            row[4] = line.split(":", 1)[-1].strip()
        elif "обед" in line:
            row[5] = line.split(":", 1)[-1].strip()
        elif "ужин" in line:
            row[6] = line.split(":", 1)[-1].strip()
        elif "перекус" in line:
            row[7] = line.split(":", 1)[-1].strip()
        elif "сладкое" in line:
            row[8] = line.split(":", 1)[-1].strip()
        elif "настроение" in line:
            row[9] = line.split(":", 1)[-1].strip()
        else:
            row[10] += line.strip() + " "

    sheet.append_row(row)
    await update.message.reply_text("✅ Данные записаны по колонкам!")
       
# Запуск приложения
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
