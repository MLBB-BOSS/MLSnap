import os
import logging
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean, func, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Налаштування бази даних
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL не знайдено. Будь ласка, встановіть його у змінних середовища.")
    exit(1)

# Замінюємо 'postgres://' на 'postgresql://', якщо необхідно
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Моделі бази даних
class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    badges = Column(String, default="")
    tasks = relationship("Task", back_populates="user")
    contributions = relationship("Contribution", back_populates="user")
    screenshots = relationship("Screenshot", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    user_id = Column(String, ForeignKey('users.user_id'))
    user = relationship("User", back_populates="tasks")

class Contribution(Base):
    __tablename__ = 'contributions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="contributions")
    task = relationship("Task")

class Screenshot(Base):
    __tablename__ = 'screenshots'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    image_data = Column(LargeBinary, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="screenshots")
    task = relationship("Task")

# Функції для роботи з базою даних
def get_session():
    return SessionLocal()

def add_badge(user, badge_name):
    badges = user.badges.split(", ") if user.badges else []
    if badge_name not in badges:
        badges.append(badge_name)
        user.badges = ", ".join(badges)

# Обробники команд та повідомлень
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or user.first_name

    user_entry = session.query(User).filter_by(user_id=user_id).first()
    if not user_entry:
        user_entry = User(user_id=user_id, username=username)
        session.add(user_entry)
        session.commit()

    session.close()

    reply_text = (
        f"Привіт, {username}! 👋\n\n"
        "Дякуємо за допомогу у зборі скріншотів персонажів.\n"
        "Ви можете переглянути свої завдання за допомогою /tasks.\n"
        "Якщо у вас виникнуть питання, скористайтесь /help."
    )

    keyboard = [
        ["Додати скріншот", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)

# Інші обробники залишаються без змін...

# Обробник помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Виникла помилка. Спробуйте пізніше.")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")
        return

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)

    application = ApplicationBuilder().token(TOKEN).build()

    # Видалення вебхука перед запуском опитування
    async def remove_webhook():
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук видалено")

    asyncio.run(remove_webhook())

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
