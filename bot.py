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
    screenshots = relationship("Screenshot", back_populates="user")  # Додано відношення до Screenshot

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

# Нова модель для збереження скріншотів
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

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    user = update.effective_user
    user_id = str(user.id)

    user_entry = session.query(User).filter_by(user_id=user_id).first()
    if not user_entry:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")
        session.close()
        return

    tasks = session.query(Task).filter_by(user_id=user_id).all()
    if not tasks:
        await update.message.reply_text("У вас немає призначених завдань.")
        session.close()
        return

    tasks_text = ""
    for task in tasks:
        status = "✅ Виконано" if task.completed else "❌ Не виконано"
        tasks_text += f"- {task.description} : {status}\n"

    await update.message.reply_text(f"Ваші завдання:\n{tasks_text}")
    session.close()

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    user = update.effective_user
    user_id = str(user.id)

    user_entry = session.query(User).filter_by(user_id=user_id).first()
    if not user_entry:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")
        session.close()
        return

    completed = session.query(Task).filter_by(user_id=user_id, completed=True).count()
    total = session.query(Task).filter_by(user_id=user_id).count()

    progress_text = f"Ви виконали {completed} з {total} завдань."
    await update.message.reply_text(progress_text)
    session.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступні команди:\n"
        "/start - Запустити бота та отримати привітання.\n"
        "/tasks - Показати ваші завдання.\n"
        "/progress - Перевірити ваш прогрес.\n"
        "/leaderboard - Показати топ учасників.\n"
        "/help - Показати це повідомлення."
    )
    await update.message.reply_text(help_text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query == "Додати скріншот":
        await update.message.reply_text("Будь ласка, надішліть скріншот.")
    elif query == "Перевірити прогрес":
        await progress_command(update, context)
    elif query in ["Команди", "Допомога"]:
        await help_command(update, context)
    else:
        await update.message.reply_text("Не зрозуміла команда. Використайте /help.")

async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Отримано запит на додавання скріншоту")
    session = get_session()
    user = update.effective_user
    user_id = str(user.id)

    try:
        user_entry = session.query(User).filter_by(user_id=user_id).first()
        if not user_entry:
            await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")
            logger.warning(f"Користувач {user_id} не знайдений у базі даних")
            return

        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            logger.info(f"Отримано фото від користувача {user_id}")

            task = session.query(Task).filter_by(user_id=user_id, completed=False).first()
            if not task:
                await update.message.reply_text("Ви виконали всі завдання!")
                logger.info(f"Користувач {user_id} не має невиконаних завдань")
                return

            # Завантаження фото у вигляді байтів
            photo_bytes = await photo_file.download_as_bytearray()
            logger.info(f"Фото успішно завантажено у вигляді байтів, розмір: {len(photo_bytes)} байт")

            # Збереження скріншоту в базу даних
            screenshot = Screenshot(
                user_id=user_id,
                task_id=task.id,
                image_data=photo_bytes
            )
            session.add(screenshot)
            logger.info(f"Скріншот додано до сесії бази даних")

            # Оновлення завдання та внесків
            task.completed = True
            contribution = Contribution(user_id=user_id, task_id=task.id)
            session.add(contribution)

            # Перевірка на баджі
            total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()
            logger.info(f"Користувач {user_id} має {total_contributions} внесків")

            if total_contributions == 5:
                add_badge(user_entry, "Початківець")
                await update.message.reply_text("Вітаємо! Ви отримали бадж **Початківець** 🎖️", parse_mode='Markdown')
                logger.info(f"Користувач {user_id} отримав бадж 'Початківець'")
            elif total_contributions == 10:
                add_badge(user_entry, "Активний")
                await update.message.reply_text("Вітаємо! Ви отримали бадж **Активний** 🎖️", parse_mode='Markdown')
                logger.info(f"Користувач {user_id} отримав бадж 'Активний'")

            session.commit()
            logger.info(f"Сесія бази даних успішно закомічена")

            await update.message.reply_text(f"Скріншот для '{task.description}' отримано та збережено! 🎉")
        else:
            await update.message.reply_text("Будь ласка, надішліть зображення у форматі фото.")
            logger.warning(f"Користувач {user_id} надіслав не фото")
    except Exception as e:
        logger.error(f"Помилка при обробці скріншоту для користувача {user_id}: {e}")
        await update.message.reply_text("Виникла помилка при збереженні скріншоту. Спробуйте ще раз.")
    finally:
        session.close()
        logger.info(f"Сесія бази даних закрита для користувача {user_id}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    top_users = session.query(User.username, func.count(Contribution.id).label('contributions')) \
                       .join(Contribution) \
                       .group_by(User.username) \
                       .order_by(func.count(Contribution.id).desc()) \
                       .limit(3).all()

    if not top_users:
        await update.message.reply_text("Наразі немає активних учасників.")
        session.close()
        return

    leaderboard_text = "🏆 **Топ 3 учасники** 🏆\n\n"
    for idx, (username, contributions) in enumerate(top_users, start=1):
        leaderboard_text += f"{idx}. {username} - {contributions} внесків\n"

    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')
    session.close()

# Обробник помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Виникла помилка. Спробуйте пізніше.")

async def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Видалення вебхука перед запуском опитування
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Вебхук видалено")

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)

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
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
