import logging
from telegram.ext import ApplicationBuilder
from config.settings import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from modules.community_collector.handlers import (
    start,
    choose_class,
    progress_command,
    help_command,
    share_progress,
    callback_query_handler,
    button_handler,
    add_screenshot,
    error_handler,
)
from modules.community_collector.scheduler import start_scheduler
from modules.community_collector.models import Base, engine
from modules.community_collector.utils import load_characters

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено.")
        return

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

    # Запуск планувальника
    start_scheduler(application)

    # Налаштування вебхука
    PORT = int(os.environ.get('PORT', '8443'))
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
