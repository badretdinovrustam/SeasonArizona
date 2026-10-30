import logging
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- НАСТРОЙКИ ---
# ВАЖНО: Перед загрузкой на Bothost замените этот токен на переменную окружения
# В коде: TOKEN = os.environ.get('TOKEN')
TOKEN = os.environ.get('9253941606:AAFzh0TadtF8G5VwtN2rJpkSoVv13ibPmJA')

# Часовой пояс для расчета понедельника (МСК)
TIMEZONE = ZoneInfo("Europe/Moscow") 

# --- ДАННЫЕ (Сезоны и Стикеры) ---
# ВНИМАНИЕ: Telegram не отправляет стикеры по эмодзи. 
# Вам нужно зайти в @BotFather, выбрать бота, /setsticker -> Season 1 и т.д., загрузить пачки стикеров.
# Затем в @userinfobot или через getUpdates получить file_id каждого стикера и вставить их ниже.
SEASONS = [
    {"name": "По инфе", "sticker_id": "file_id_для_телефона"}, 
    {"name": "Скорострелы", "sticker_id": "file_id_для_ноутбука"},
    {"name": "Автогонки", "sticker_id": "file_id_для_машины"},
    {"name": "По новому", "sticker_id": "file_id_для_вертолета"},
    {"name": "Мотогонки", "sticker_id": "file_id_для_мото"},
]

# --- ДАННЫЕ (33 Сервера) ---
SERVERS = {
    1: {"name": "[Phoenix]", "season": "По новому"},
    2: {"name": "[Tucson]", "season": "По инфе"},
    3: {"name": "[Scottdale]", "season": "Скорострелы"},
    4: {"name": "[Chandler]", "season": "По инфе"},
    5: {"name": "[Brainburg]", "season": "По новому"},
    6: {"name": "[Saint Rose]", "season": "По новому"},
    7: {"name": "[Mesa]", "season": "Автогонки"},
    8: {"name": "[Red-Rock]", "season": "Скорострелы"},
    9: {"name": "[Yuma]", "season": "По новому"},
    10: {"name": "[Surprise]", "season": "Скорострелы"},
    11: {"name": "[Prescott]", "season": "По инфе"},
    12: {"name": "[Glendale]", "season": "Скорострелы"},
    13: {"name": "[Kingman]", "season": "Мотогонки"},
    14: {"name": "[Winslow]", "season": "Автогонки"},
    15: {"name": "[Payson]", "season": "Автогонки"},
    16: {"name": "[Gilbert]", "season": "Мотогонки"},
    17: {"name": "[Show Low]", "season": "Мотогонки"},
    18: {"name": "[Casa-Grande]", "season": "Мотогонки"},
    19: {"name": "[Page]", "season": "По инфе"},
    20: {"name": "[Sun-City]", "season": "Автогонки"},
    21: {"name": "[Queen-Creek]", "season": "Мотогонки"},
    22: {"name": "[Sedona]", "season": "По инфе"},
    23: {"name": "[Holiday]", "season": "По новому"},
    24: {"name": "[Wednesday]", "season": "Скорострелы"},
    25: {"name": "[Yava]", "season": "Скорострелы"},
    26: {"name": "[Faraway]", "season": "Скорострелы"},
    27: {"name": "[Bumble Bee]", "season": "Мотогонки"},
    28: {"name": "[Christmas]", "season": "Скорострелы"},
    29: {"name": "[Mirage]", "season": "Скорострелы"},
    30: {"name": "[Love]", "season": "Скорострелы"},
    31: {"name": "[Drake]", "season": "Скорострелы"},
    32: {"name": "[Space]", "season": "Мотогонки"},
    33: {"name": "[Home]", "season": "По инфе"},
}

# --- ЛОГИКА ОБНОВЛЕНИЯ СЕЗОНОВ ---

def get_next_monday_midnight(now: datetime) -> datetime:
    days_ahead = (7 - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
    return next_monday.astimezone(TIMEZONE)

def update_server_seasons():
    for server_id in SERVERS:
        current_season_name = SERVERS[server_id]["season"]
        current_index = next((i for i, s in enumerate(SEASONS) if s["name"] == current_season_name), None)
        
        if current_index is not None:
            next_index = (current_index + 1) % len(SEASONS)
            SERVERS[server_id]["season"] = SEASONS[next_index]["name"]
    logging.info("Сезоны на всех серверах успешно обновлены.")

async def schedule_season_update(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)
    next_run_time = get_next_monday_midnight(now)
    
    await context.job_queue.run_daily(
        callback=job_update_seasons,
        time=next_run_time.time(),
        days=(0,),  # 0 - это понедельник
        name="season_updater"
    )
    logging.info(f"Следующее обновление сезонов запланировано на: {next_run_time}")

async def job_update_seasons(context: ContextTypes.DEFAULT_TYPE):
    update_server_seasons()
    logging.info("Еженедельная задача: сезоны обновлены.")

# --- КОМАНДЫ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Показать сезоны", callback_data="show_seasons")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот для отслеживания сезонов Arizona RP.", 
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_seasons":
        message_lines = ["🗺️ *Текущие сезоны на серверах Arizona RP:*", ""]
        
        for server_id in sorted(SERVERS.keys()):
            server = SERVERS[server_id]
            season_name = server["season"]
            season_info = next(s for s in SEASONS if s["name"] == season_name)
            
            line = f"{server['name']} — {season_name}"
            message_lines.append(line)
        
        text = "\n".join(message_lines)
        await query.message.edit_text(text, parse_mode="Markdown")
        
        # Отправляем стикеры (по одному на сервер, это может занять время)
        for server_id in sorted(SERVERS.keys()):
            server = SERVERS[server_id]
            season_name = server["season"]
            season_info = next(s for s in SEASONS if s["name"] == season_name)
            
            # Проверка, что file_id не является заглушкой
            if season_info["sticker_id"] != "file_id_для_...":
                try:
                    await context.bot.send_sticker(
                        chat_id=update.effective_chat.id,
                        sticker=season_info["sticker_id"]
                    )
                except Exception as e:
                    logging.error(f"Ошибка отправки стикера для {server['name']}: {e}")

# --- ЗАПУСК ---

def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    # Запускаем планировщик задач
    app.job_queue.run_once(schedule_season_update, 1)

    # Запуск на Bothost (порт 8000)
    app.run_webhook(
        listen="0.0.0.0",
        port=8000,
        url_path=TOKEN,
        # Эта строка будет работать, когда вы настроите домен на Bothost
        # webhook_url="https://ВАШ_ДОМЕН.bothost.ru/" + TOKEN 
    )

if __name__ == "__main__":
    main()