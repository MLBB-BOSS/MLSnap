from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, MessageHandler, filters, ContextTypes
import json
import os

# Ім'я файлу для зберігання прогресу
PROGRESS_FILE = "progress.json"

# Список користувачів і їх завдання
users = {
    "@anwesxx": {"name": "Анна", "tasks": []},
    "@Undertaker_A": {"name": "Михайло", "tasks": []},
    "@Konnerpo": {"name": "Артем", "tasks": []},
    "@chaos_queen_fs": {"name": "Монорочка", "tasks": []},
    "@Lyoha221": {"name": "Льоха", "tasks": []},
    "@PeachBombastic": {"name": "Peach", "tasks": []},
    "@Kvas_Enjoyer": {"name": "Квасовий поціновувач", "tasks": []},
    "@HOMYARCHOK": {"name": "Хом'як", "tasks": []},
    "@lilTitanlil": {"name": "Малий Титан", "tasks": []},
    "@Crysun": {"name": "Кріс", "tasks": []},
    "@is_mlbb": {"name": "Олег", "tasks": []}
}

# Ініціалізація прогресу
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {user: {"tasks_completed": []} for user in users}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

progress = load_progress()

# Привітання користувача
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        welcome_message = f"Привіт, {users[user_id]['name']}! Дякую за допомогу! 😊\n" \
                          f"Ваше завдання — зробити скріншоти обраних персонажів. Щоб переглянути, які скріншоти потрібно додати, " \
                          f"введіть /tasks."
        await update.message.reply_text(welcome_message)
    else:
        await update.message.reply_text("Привіт! Ви не вказані в списку учасників, але можете допомогти!")

# Показ завдань для кожного користувача
async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        tasks_needed = [task for task in users[user_id]["tasks"] if task not in progress[user_id]["tasks_completed"]]
        task_list = "\n".join(tasks_needed) if tasks_needed else "Усі скріншоти вже додані. Дякуємо!"
        await update.message.reply_text(f"Ваші завдання:\n{task_list}")
    else:
        await update.message.reply_text("Привіт! Ви не маєте призначених завдань.")

# Обробка додавання скріншотів
async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        if update.message.photo:
            # Отримання останнього фото з повідомлення
            photo_file = await update.message.photo[-1].get_file()
            filename = f"{user_id}_{len(progress[user_id]['tasks_completed']) + 1}.jpg"
            photo_file.download(filename)

            # Оновлення прогресу
            progress[user_id]["tasks_completed"].append(filename)
            save_progress(progress)

            await update.message.reply_text("Скріншот отримано! Дякую за допомогу!")
        else:
            await update.message.reply_text("Будь ласка, надішліть зображення.")
    else:
        await update.message.reply_text("Ви не вказані в списку учасників.")

def main():
    # Створення застосунку бота
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Додавання команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tasks", tasks))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
