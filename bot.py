import os
import json
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters, CallbackContext

# Отримання токена з середовища Heroku
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
def start(update: Update, context: CallbackContext):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        welcome_message = f"Привіт, {users[user_id]['name']}! Дякую за допомогу! 😊\n" \
                          f"Ваше завдання — зробити скріншоти обраних персонажів. Щоб переглянути, які скріншоти потрібно додати, " \
                          f"введіть /tasks."
        keyboard = [['Додати скріншот', 'Перевірити прогрес'], ['Команди', 'Допомога']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Привіт! Ви не вказані в списку учасників, але можете допомогти!")

# Показ завдань для кожного користувача
def tasks(update: Update, context: CallbackContext):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        tasks_needed = [task for task in users[user_id]["tasks"] if task not in progress[user_id]["tasks_completed"]]
        task_list = "\n".join(tasks_needed) if tasks_needed else "Усі скріншоти вже додані. Дякуємо!"
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ваші завдання:\n{task_list}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Привіт! Ви не маєте призначених завдань.")

# Обробка додавання скріншотів
def add_screenshot(update: Update, context: CallbackContext):
    user_id = f"@{update.message.from_user.username}"
    if user_id in users:
        if update.message.photo:
            # Отримання першого фото з повідомлення
            photo_file = update.message.photo[-1].get_file()
            filename = f"{user_id}_{len(progress[user_id]['tasks_completed']) + 1}.jpg"
            photo_file.download(filename)

            # Оновлення прогресу
            progress[user_id]["tasks_completed"].append(filename)
            save_progress(progress)

            context.bot.send_message(chat_id=update.effective_chat.id, text="Скріншот отримано! Дякую за допомогу!")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Будь ласка, надішліть зображення.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Ви не вказані в списку учасників.")

def help_command(update: Update, context: CallbackContext):
    help_text = "Команди бота:\n" \
                "/start - Почати роботу\n" \
                "/tasks - Показати завдання\n" \
                "Надішліть зображення, щоб додати скріншот."
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("tasks", tasks))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.photo, add_screenshot))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex("^(Додати скріншот)$"), add_screenshot))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex("^(Перевірити прогрес)$"), tasks))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex("^(Команди|Допомога)$"), help_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
