import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets подключение
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.environ["SPREADSHEET_URL"]).sheet1

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пиши данные за день (вода, питание, настроение и т.д.), я всё сохраню.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    row = [""] * 11  # Количество колонок

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
