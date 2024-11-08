import os
from telegram import Update, Bot
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters, CallbackContext

# Отримання токена з середовища Heroku
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привіт! Я готовий допомогти тобі з зображеннями героїв.")

def add_screenshot(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Скріншот отримано. Дякуємо за допомогу!")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Додавання команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, add_screenshot))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
