import os
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, MessageHandler, filters, ContextTypes

# Отримання токена з середовища Heroku
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Створення папки для збереження зображень
if not os.path.exists("screenshots"):
    os.makedirs("screenshots")

# Список користувачів і хештегів
users = {
    "@anwesxx": "Анна",
    "@Undertaker_A": "Михайло",
    "@Konnerpo": "Артем",
    "@chaos_queen_fs": "Монорочка",
    "@Lyoha221": "Льоха",
    "@PeachBombastic": "Peach",
    "@Kvas_Enjoyer": "Квасовий поціновувач",
    "@HOMYARCHOK": "Хом'як",
    "@lilTitanlil": "Малий Титан",
    "@Crysun": "Кріс",
    "@is_mlbb": "Олег"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.username
    if user_id in users:
        welcome_message = f"Привіт, {users[user_id]}! Раді бачити тебе тут!"
        await update.message.reply_text(welcome_message)
    else:
        await update.message.reply_text("Привіт! Ви не вказані в списку користувачів.")

async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.username
    user_name = users.get(user_id, "друг")

    if update.message.photo:
        # Отримання останнього зображення (вищої якості)
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"screenshots/{user_id}_{photo_file.file_unique_id}.jpg"
        
        # Збереження зображення
        await photo_file.download(file_path)
        await update.message.reply_text(f"Скріншот отримано від {user_name}. Дякуємо за допомогу!")
    else:
        await update.message.reply_text("Будь ласка, надішліть зображення.")

def main():
    # Створення застосунку бота
    application = Application.builder().token(TOKEN).build()

    # Додавання команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
