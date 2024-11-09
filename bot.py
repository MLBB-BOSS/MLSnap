import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
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
    logger.info("Замінено 'postgres://' на 'postgresql://' у DATABASE_URL")

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

# Ініціалізація списку персонажів
HEROES = {
    "Fighter": ["Balmond", "Alucard", "Bane", "Zilong", "Freya"],
    "Tank": ["Alice", "Tigreal", "Akai", "Franco", "Minotaur"],
    "Assassin": ["Saber", "Alucard", "Zilong", "Fanny", "Natalia"],
    "Marksman": ["Popol and Kupa", "Brody", "Beatrix", "Natan", "Melissa"],
    "Mage": ["Vale", "Lunox", "Kadita", "Cecillion", "Luo Yi"],
    "Support": ["Rafaela", "Minotaur", "Lolita", "Estes", "Angela"],
}

# Функція для відображення головного меню
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
        "Ласкаво просимо до меню вибору персонажів та завдань."
    )
    keyboard = [
        ["Вибрати персонажа", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)

# Функція для відображення меню з вибором персонажів
async def choose_hero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[hero for hero in heroes] for heroes in HEROES.values()]
    keyboard.append(["Повернутися до головного меню"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Оберіть персонажа:", reply_markup=reply_markup)

# Обробник для вибору персонажа
async def handle_hero_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_hero = update.message.text
    if selected_hero in sum(HEROES.values(), []):
        await update.message.reply_text(f"Ви вибрали {selected_hero}. Надішліть скріншот, якщо готові.")
    elif selected_hero == "Повернутися до головного меню":
        await start(update, context)
    else:
        await update.message.reply_text("Обраний персонаж не знайдений. Спробуйте ще раз або скористайтеся /help.")

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
        "/start - Головне меню.\n"
        "/choose_hero - Вибір персонажа.\n"
        "/progress - Перевірити прогрес.\n"
        "/help - Показати це повідомлення."
    )
    await update.message.reply_text(help_text)

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("choose_hero", choose_hero))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hero_selection))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
