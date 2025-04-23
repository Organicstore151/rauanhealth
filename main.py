import os
import json
from openai import OpenAI
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Google Sheets подключение
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.environ["SPREADSHEET_URL"]).sheet1

DAY_NAMES = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}

# === МЕНЮ ПО ДНЯМ ===
AIP_BREAKFASTS = {
    0: "Тунец (100 г), гречка (150 г), яйцо (1 шт.), авокадо (40 г), оливковое масло (1 ст.л.)",
    1: "Куриное филе (100 г), макароны амарантовые (180 г), яйцо (1 шт.), брокколи и цветная капуста (по 80 г), оливковое масло (1 ст.л.)",
    2: "Судак (100 г), пшено (160 г), яйцо (1 шт.), салат из огурца, салата и авокадо (50 г), оливковое масло (1 ст.л.)",
    3: "Сёмга (100 г), смесь бурого и дикого риса (150 г), салат с авокадо и листовым салатом, оливковое масло (1 ст.л.)",
    4: "Омлет из 3 яиц и 30 мл растительного молока, киноа (160 г), салат с авокадо (40 г), сёмга (50 г), оливковое масло (1 ст.л.)",
    5: "Сёмга (100 г), пшено (150 г), яйцо (1 шт.), салат с огурцом, авокадо и кедровыми орешками (10 г), оливковое масло (1 ст.л.)",
    6: "Яйца (2 шт.), минтай (70 г), бурый рис (150 г), тыква запечённая (100 г), авокадо (50 г), оливковое масло (1 ст.л.)"
}
AIP_SNACKS = {
    0: "Яйца (2 шт.), киноа (180 г), цветная капуста (100 г), брюссельская капуста (100 г), грецкий орех (15 г)",
    1: "Гречка (180 г), растительное молоко (100 мл), куриное филе (100 г), яйцо (1 шт.), морковь (75 г), бразильский орех (4 шт.)",
    2: "Судак (90 г), киноа (180 г), тыква (150 г), грецкий орех (20 г), огурец (100 г)",
    3: "Индейка (90 г), смесь бурого и дикого риса (180 г), овощи (брокколи, цветная капуста, кабачок – 150 г), авокадо (50 г)",
    4: "Семга (90 г), киноа (180 г), цуккини (100 г), огурец (150 г), оливковое/льняное масло (1 ст.л.)",
    5: "Индейка (90 г), гречка (180 г), брокколи (150 г), цветная капуста (100 г), авокадо (40 г)",
    6: "Минтай (90 г), пшено (180 г), яйцо (1 шт.), курага (20 г), кедровые орехи (10 г)"
}
AIP_LUNCHES = {
    0: "Куриное филе (100 г), бурый рис (180 г), кабачок, брокколи, цветная капуста — по 70 г, курага (15 г), грецкий орех (10 г), оливковое масло (1 ст.л.)",
    1: "Говядина (90 г), киноа (180 г), свекла (150 г), морковь (75 г), огурец (100 г), оливковое масло (1 ст.л.)",
    2: "Индейка (90 г), пшено (180 г), капусты: белокочанная и брюссельская – 240 г, курага (20 г)",
    3: "Индейка (90 г), гречка (180 г), свекла (150 г), грецкий орех (20 г)",
    4: "Мясо кролика (90 г), макароны амарантовые (180 г), салат: огурец (100 г), салат листовой (20 г), цуккини (100 г)",
    5: "Индейка (90 г), пшено (180 г), брокколи, цветная капуста, капуста белокочанная – всего 300 г",
    6: "Кролик (100 г), гречка (180 г), тыква (200 г), огурец (150 г), оливковое масло (1 ст.л.)"
}
AIP_DINNERS = {
    0: "Треска (100 г), гречка (180 г), цуккини (200 г), авокадо (50 г), яблоко (150 г)",
    1: "Судак (90 г), макароны амарантовые (180 г), авокадо (50 г), огурец (100 г), зелень",
    2: "Куриное филе (90 г), рис (180 г), брокколи и цветная капуста (150 г), грецкий орех (15 г)",
    3: "Минтай (90 г), смесь бурого и дикого риса (180 г), брокколи, цветная капуста, кабачок – 210 г, авокадо (50 г)",
    4: "Куриное филе (90 г), киноа (180 г), салат: свекла варёная (100 г), морковь свежая (100 г), курага (20 г)",
    5: "Куриное филе (80 г), смесь бурого и дикого риса (180 г), кабачок (100 г), авокадо (40 г)",
    6: "Минтай (90 г), рис бурый (180 г), морковь (150 г), авокадо (40 г)"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🍽️ Завтрак"), KeyboardButton("🥜 Перекус")],
        [KeyboardButton("🍲 Обед"), KeyboardButton("🌙 Ужин")],
        [KeyboardButton("📝 Отчёт по здоровью"), KeyboardButton("📈 Прогресс недели")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Выбери действие или пиши данные вручную:", reply_markup=reply_markup)

async def send_meal(update: Update, context: ContextTypes.DEFAULT_TYPE, meal_type: str):
    day_idx = datetime.now().weekday()
    day_name = DAY_NAMES[day_idx]
    meal_dicts = {
        "🍽️ завтрак": AIP_BREAKFASTS,
        "🥜 перекус": AIP_SNACKS,
        "🍲 обед": AIP_LUNCHES,
        "🌙 ужин": AIP_DINNERS
    }
    label = meal_type.lower()
    meal = meal_dicts[label].get(day_idx, "Нет меню на сегодня.")

    await update.message.reply_text(f"📅 Сегодня {day_name}\n\n{label.capitalize()}:\n{meal}")

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"Ты — бот-диетолог. Дай короткую, полезную рекомендацию перед {label}, подходящую для AIP и набора массы. Будь мотивирующим."
            },
            {
                "role": "user",
                "content": f"Сегодня {day_name}. Сейчас {label}. Что мне стоит учесть перед этим приёмом пищи?"
            }
        ]
    )
    reply = response.choices[0].message.content
    await update.message.reply_text(f"💡 {reply}")

async def weekly_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Анализирую твою неделю...")

    data = sheet.get_all_values()
    rows = data[-7:] if len(data) > 7 else data[1:]

    water_list, mood_list = [], []
    stool_days, activity_days = 0, 0
    meals = []

    for row in rows:
        try:
            water = row[2].replace(",", ".").strip()
            water_list.append(float(water))
        except: pass

        if "да" in row[1].strip().lower() or "был" in row[1].strip().lower():
            stool_days += 1
        if row[3].strip():
            activity_days += 1
        try:
            mood_list.append(int(row[9].strip()))
        except: pass

        meals.extend([
            "🍽️ Завтрак: " + row[4],
            "🍲 Обед: " + row[5],
            "🌙 Ужин: " + row[6],
            "🥜 Перекусы: " + row[7],
            "☕ Сладкое / напитки: " + row[8], ""
        ])

    summary = f"""Статистика за неделю:
- 💧 Вода: {round(sum(water_list)/len(water_list), 2) if water_list else 'нет данных'} л/день
- 🚽 Стул: {stool_days} дней из 7
- 🤸 Движение: {activity_days} дней
- 🙂 Настроение: {round(sum(mood_list)/len(mood_list), 1) if mood_list else 'нет данных'} / 10
\nПитание по дням:\n{chr(10).join(meals)}"""

    await update.message.reply_text(summary)

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Ты — заботливый бот-диетолог. На основе данных по воде, стулу, активности, настроению и питанию за неделю — дай 3–5 персональных рекомендаций. Пиши дружелюбно, конкретно, с эмодзи."
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

    if "завтрак" in text:
        await send_meal(update, context, "🍽️ завтрак")
        return
    if "перекус" in text:
        await send_meal(update, context, "🥜 перекус")
        return
    if "обед" in text:
        await send_meal(update, context, "🍲 обед")
        return
    if "ужин" in text:
        await send_meal(update, context, "🌙 ужин")
        return
    if "прогресс недели" in text:
        await weekly_progress(update, context)
        return
    if "отчёт по здоровью" in text or "отчет по здоровью" in text:
        await update.message.reply_text(
            "📝 Вот шаблон для отчёта. Просто дополни и отправь:\n\n"
            "Завтрак: ...\nОбед: ...\nУжин: ...\nПерекусы: ...\nСладкое / напитки: ...\n"
            "Вода: ...\nСтул: ...\nДвижение: ...\nНастроение: ..."
        )
        return

    row = ["" for _ in range(11)]
    row[0] = datetime.now().strftime("%Y-%m-%d")
    for line in text.split('\n'):
        for idx, key in enumerate(["стул", "вода", "движение", "завтрак", "обед", "ужин", "перекус", "сладкое", "настроение"]):
            if key in line:
                row[idx+1] = line.split(":", 1)[-1].strip()
                break
        else:
            row[10] += line.strip() + " "

    sheet.append_row(row)
    await update.message.reply_text("✅ Данные записаны по колонкам!")

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
