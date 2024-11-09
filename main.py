# main.py
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from modules.community_collector.handlers import (
    start, choose_class, progress_command, help_command,
    share_progress, callback_query_handler, button_handler,
    add_screenshot, send_weekly_reports, error_handler
)
from modules.community_collector.utils import load_characters, engine
from modules.community_collector.models import Base
from config.settings import TELEGRAM_BOT_TOKEN, logger

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)
    # Завантаження персонажів до бази даних
    load_characters()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("choose_class", choose_class))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("share", share_progress))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))

    # Обробник помилок
    application.add_error_handler(error_handler)

    # Налаштування планувальника
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_weekly_reports, 'interval', weeks=1, args=[application.bot])
    scheduler.start()

    # Запуск бота
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
