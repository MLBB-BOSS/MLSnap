import os
import logging

logger = logging.getLogger(__name__)

# Отримуємо змінні середовища
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("https://git.heroku.com/mlbb.git")  # Додано

# Замінюємо 'postgres://' на 'postgresql://', якщо необхідно
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Замінено 'postgres://' на 'postgresql://' у DATABASE_URL")
