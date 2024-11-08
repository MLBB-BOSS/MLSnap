import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Завантаження змінних середовища з .env файлу
load_dotenv()

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ім'я файлу для збереження прогресу
PROGRESS_FILE = "progress.json"
# Папка для збереження скріншотів
SCREENSHOTS_DIR = "screenshots"

# Ініціалізація прогресу
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

# Ініціалізація завдань (можна адаптувати під реальні герої)
TASKS = {
    "user1": ["Герой A", "Герой B", "Герой C"],
    "user2": ["Герой D", "Герой E", "Герой F"],
    # Додайте інших користувачів та їх завдання
}

# Створення папки для скріншотів, якщо не існує
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    username = user.username if user.username else user.first_name
    user_id = str(user.id)
    
    progress = load_progress()
    
    if user_id not in progress:
        # Призначення завдань користувачу (можна реалізувати більш динамічно)
        progress[user_id] = {
            "username": username,
            "tasks": TASKS.get(username, ["Герой A", "Герой B", "Герой C"]),
            "completed": []
        }
        save_progress(progress)
    
    reply_text = (
        f"Привіт, {username}! 👋\n\n"
        "Дякуємо за допомогу у зборі скріншотів персонажів з Mobile Legends.\n"
        "Ви можете переглянути свої завдання за допомогою /tasks.\n"
        "Якщо у вас виникнуть питання, скористайтесь /help."
    )
    
    # Створення клавіатури з кнопками
    keyboard = [
        ["Додати скріншот", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(reply_text, reply_markup=reply_markup)

# Обробник команди /tasks
async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    progress = load_progress()
    
    if user_id in progress:
        tasks = progress[user_id]["tasks"]
        tasks_text = "\n".join([f"- {task}" for task in tasks])
        await update.message.reply_text(f"Ваші завдання:\n{tasks_text}")
    else:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")

# Обробник команди /progress
async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    progress = load_progress()
    
    if user_id in progress:
        completed = progress[user_id]["completed"]
        total = len(progress[user_id]["tasks"])
        progress_text = f"Ви виконали {len(completed)}/{total} завдань."
        if completed:
            completed_tasks = "\n".join([f"- {task}" for task in completed])
            progress_text += f"\n\nЗавершені завдання:\n{completed_tasks}"
        await update.message.reply_text(progress_text)
    else:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")

# Обробник команди /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Доступні команди:\n"
        "/start - Запустити бота та отримати привітання.\n"
        "/tasks - Показати ваші завдання.\n"
        "/progress - Перевірити ваш прогрес.\n"
        "/help - Показати це повідомлення."
    )
    await update.message.reply_text(help_text)

# Обробник кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text
    if query == "Додати скріншот":
        await update.message.reply_text("Будь ласка, надішліть скріншот персонажа.")
    elif query == "Перевірити прогрес":
        await progress_command(update, context)
    elif query == "Команди":
        await help_command(update, context)
    elif query == "Допомога":
        await help_command(update, context)
    else:
        await update.message.reply_text("Не зрозуміла команда. Використайте /help для списку доступних команд.")

# Обробник додавання скріншоту
async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    progress = load_progress()
    
    if user_id not in progress:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")
        return
    
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        task_list = progress[user_id]["tasks"]
        completed = progress[user_id]["completed"]
        
        # Визначення наступного завдання
        remaining_tasks = [task for task in task_list if task not in completed]
        if not remaining_tasks:
            await update.message.reply_text("Ви вже виконали всі завдання. Дякуємо за участь!")
            return
        
        current_task = remaining_tasks[0]
        filename = f"{user_id}_{current_task.replace(' ', '_')}.jpg"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        await photo_file.download_to_drive(filepath)
        
        # Оновлення прогресу
        progress[user_id]["completed"].append(current_task)
        save_progress(progress)
        
        await update.message.reply_text(f"Скріншот для '{current_task}' отримано! 🎉")
    else:
        await update.message.reply_text("Будь ласка, надішліть зображення у форматі фото.")

# Основна функція запуску бота
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено в змінних середовища.")
        return
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Додавання обробників команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обробник кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    
    # Обробник фотографій
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
