import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.environ["SPREADSHEET_URL"]).sheet1

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пиши сюда питание, воду, настроение и стул — я всё сохраню в таблицу.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    sheet.append_row([text])
    await update.message.reply_text("✅ Данные записаны!")

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
