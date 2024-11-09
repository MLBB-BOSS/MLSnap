# config/settings.py
import os
import logging

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Налаштування бази даних
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL не знайдено. Будь ласка, встановіть його на Heroku.")
    exit(1)

# Замінюємо 'postgres://' на 'postgresql://', якщо необхідно
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Замінено 'postgres://' на 'postgresql://' у DATABASE_URL")

# Токен Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не встановлено.")
    exit(1)
