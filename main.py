import os
import json
from openai import OpenAI
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import ReplyKeyboardMarkup, KeyboardButton
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Google Sheets подключение
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.environ["SPREADSHEET_URL"]).sheet1

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   keyboard = [
    [KeyboardButton("🌅 Утро")],
    [KeyboardButton("📝 Отчёт по здоровью")],
    [KeyboardButton("📈 Прогресс недели")]
]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Выбери действие или пиши данные вручную:",
        reply_markup=reply_markup
    )
# Обработка обычных сообщений
from datetime import datetime

AIP_BREAKFASTS = {
    0: "Тунец (70 г), гречка (220 г), авокадо (40 г), оливковое масло (1 ст.л.)",
    1: "Куриное филе (70 г), яйцо (1 шт.), брокколи (100 г), цветная капуста (100 г), амарантовые макароны (220 г)",
    2: "Судак тушёный (70 г), пшено (220 г), салат из огурца и авокадо (50 г), оливковое масло (1 ст.л.)",
    3: "Сёмга (80 г), бурый и дикий рис (220 г), салат: огурец, листовой салат, грецкий орех (20 г)",
    4: "Омлет из 3 яиц с растительным молоком, киноа (220 г), салат из огурца, авокадо и салата",
    5: "Салат с сёмгой, айсберг, огурец, авокадо, кедровые орешки (10 г), пшено (220 г), оливковое масло (1 ст.л.)",
    6: "Яйца (2 шт.), тушёные овощи (кабачок, брокколи, цветная капуста), бурый рис (220 г), тыква запечённая (100 г)"
}

DAY_NAMES = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}
async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Подбираю рекомендации...")

    day_idx = datetime.now().weekday()
    day_name = DAY_NAMES[day_idx]
    aip_breakfast = AIP_BREAKFASTS[day_idx]

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly assistant helping a person who follows the Autoimmune Protocol (AIP). "
                    "They eat 4 times a day (~2400 kcal total), ~600 kcal for breakfast. They avoid gluten, dairy, sugar, nightshades, legumes. "
                    "They suffer from constipation, take medicine in the morning, and do back/spine exercises. "
                    f"Today is {day_name}. Use this breakfast example in your response: {aip_breakfast}. "
                    "Give a step-by-step morning plan (1, 2, 3...), including: hydration, medicine, breakfast, back exercises. "
                    "Be clear, warm, use emojis, and finish with motivation."
                )
            },
            {
                "role": "user",
                "content": "Доброе утро. Дай мне рекомендации на сегодня для энергии, пищеварения и спины."
            }
        ]
    )

    reply = response.choices[0].message.content
    await update.message.reply_text(reply)

async def weekly_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Анализирую твою неделю...")

    data = sheet.get_all_values()
    headers = data[0]
    rows = data[-7:] if len(data) > 7 else data[1:]

    water_list = []
    stool_days = 0
    mood_list = []
    activity_days = 0
    meals = []

    for row in rows:
        water = row[2].replace(",", ".").strip()
        stool = row[1].strip().lower()
        movement = row[3].strip()
        mood = row[9].strip()

        try:
            water_list.append(float(water))
        except:
            pass

        if "да" in stool or "был" in stool:
            stool_days += 1

        if movement:
            activity_days += 1

        try:
            mood_list.append(int(mood))
        except:
            pass

        meals.append("🍽️ Завтрак: " + row[4])
        meals.append("🍲 Обед: " + row[5])
        meals.append("🌙 Ужин: " + row[6])
        meals.append("🥜 Перекусы: " + row[7])
        meals.append("☕ Сладкое / напитки: " + row[8])
        meals.append("")

    meal_text = "\n".join(meals)

    summary = f"""Статистика за неделю:
- 💧 Вода: {round(sum(water_list)/len(water_list), 2) if water_list else 'нет данных'} л/день
- 🚽 Стул: {stool_days} дней из 7
- 🤸 Движение: {activity_days} дней
- 🙂 Настроение: {round(sum(mood_list)/len(mood_list), 1) if mood_list else 'нет данных'} / 10

Питание по дням:
{meal_text}
"""

    await update.message.reply_text(summary)

    # GPT-рекомендации
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — заботливый бот-диетолог. На основе данных по воде, стулу, активности, настроению и питанию за неделю — "
                    "дай 3–5 персональных рекомендаций. Пиши дружелюбно, конкретно, с эмодзи."
                )
            },
            {
                "role": "user",
                "content": f"Вот мои данные за неделю:\n{summary}\nЧто ты можешь мне порекомендовать?"
            }
        ]
    )

    reply = response.choices[0].message.content
    await update.message.reply_text("💡 Рекомендации:\n" + reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "прогресс недели" in text:
        await weekly_progress(update, context)
        return

    if "отчёт по здоровью" in text or "отчет по здоровью" in text:
        await update.message.reply_text(
            "📝 Вот шаблон для отчёта. Просто дополни и отправь:\n\n"
            "Завтрак: ...\n"
            "Обед: ...\n"
            "Ужин: ...\n"
            "Перекусы: ...\n"
            "Сладкое / напитки: ...\n"
            "Вода: ...\n"
            "Стул: ...\n"
            "Движение: ...\n"
            "Настроение: ...\n"
        )
        return

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
