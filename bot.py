import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
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

# Стан для розмови
CHOOSE_CLASS, CHOOSE_HERO, AWAIT_SCREENSHOT = range(3)

# Функція для відображення головного меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_text = (
        "Ласкаво просимо до меню вибору персонажів та завдань.\n\n"
        "Оберіть клас персонажів для початку."
    )
    keyboard = [[hero_class] for hero_class in HEROES.keys()]
    keyboard.append(["Повернутися до головного меню"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)
    return CHOOSE_CLASS

# Обробник для вибору класу
async def choose_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_class = update.message.text
    context.user_data['selected_class'] = selected_class

    if selected_class in HEROES:
        keyboard = [[hero] for hero in HEROES[selected_class]]
        keyboard.append(["Повернутися до вибору класу"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Оберіть персонажа з класу {selected_class}:", reply_markup=reply_markup)
        return CHOOSE_HERO
    else:
        await update.message.reply_text("Будь ласка, оберіть один із доступних класів.")
        return CHOOSE_CLASS

# Обробник для вибору персонажа
async def choose_hero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_hero = update.message.text
    context.user_data['selected_hero'] = selected_hero

    if selected_hero in sum(HEROES.values(), []):
        await update.message.reply_text(
            f"Ви вибрали {selected_hero}. Надішліть скріншот або поверніться до вибору класу чи персонажа.",
            reply_markup=ReplyKeyboardMarkup([["Повернутися до вибору класу"]], resize_keyboard=True)
        )
        return AWAIT_SCREENSHOT
    else:
        await update.message.reply_text("Будь ласка, оберіть персонажа зі списку.")
        return CHOOSE_HERO

# Обробник для отримання скріншоту
async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    selected_hero = context.user_data['selected_hero']
    
    session = get_session()
    # Збереження скріншоту в базу даних
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        screenshot = Screenshot(
            user_id=user_id,
            task_id=None,  # Завдання можна налаштувати окремо
            image_data=photo_bytes
        )
        session.add(screenshot)
        session.commit()
        await update.message.reply_text(f"Скріншот для персонажа {selected_hero} отримано та збережено!")
    else:
        await update.message.reply_text("Будь ласка, надішліть фото у вигляді зображення.")
    
    session.close()
    return ConversationHandler.END

# Функція для повернення в головне меню
async def return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return CHOOSE_CLASS

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)

    # Створення обробника розмови
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CLASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_class)
            ],
            CHOOSE_HERO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_hero)
            ],
            AWAIT_SCREENSHOT: [
                MessageHandler(filters.PHOTO, receive_screenshot),
                MessageHandler(filters.TEXT, return_to_main_menu)
            ],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, return_to_main_menu)]
    )

    # Додавання обробників
    # Додавання обробників для інших команд
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

    #
