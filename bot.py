import os
from telegram import Update, Bot
from telegram.ext import CommandHandler, Application, MessageHandler, filters, ContextTypes

# Отримання токена з середовища Heroku
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привіт! Я готовий допомогти тобі з зображеннями героїв.")

async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Скріншот отримано. Дякуємо за допомогу!")

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
