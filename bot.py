import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, func, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
    contributions = relationship("Contribution", back_populates="user")
    screenshots = relationship("Screenshot", back_populates="user")

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    screenshots = relationship("Screenshot", back_populates="character")

class Contribution(Base):
    __tablename__ = 'contributions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    character_id = Column(Integer, ForeignKey('characters.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="contributions")
    character = relationship("Character")

class Screenshot(Base):
    __tablename__ = 'screenshots'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    character_id = Column(Integer, ForeignKey('characters.id'))
    image_data = Column(LargeBinary, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="screenshots")
    character = relationship("Character", back_populates="screenshots")

# Функції для роботи з базою даних
def get_session():
    return SessionLocal()

def add_badge(user, badge_name):
    badges = user.badges.split(", ") if user.badges else []
    if badge_name not in badges:
        badges.append(badge_name)
        user.badges = ", ".join(badges)

def load_characters():
    session = get_session()
    existing_characters = session.query(Character).count()
    if existing_characters == 0:
        # Перелік персонажів за класами
        characters_data = [
            # Fighter
            {"name": "Balmond", "role": "Fighter"},
            {"name": "Alucard", "role": "Fighter"},
            {"name": "Bane", "role": "Fighter"},
            {"name": "Zilong", "role": "Fighter"},
            {"name": "Freya", "role": "Fighter"},
            {"name": "Alpha", "role": "Fighter"},
            {"name": "Ruby", "role": "Fighter"},
            {"name": "Roger", "role": "Fighter"},
            {"name": "Gatotkaca", "role": "Fighter"},
            {"name": "Jawhead", "role": "Fighter"},
            {"name": "Martis", "role": "Fighter"},
            {"name": "Aldous", "role": "Fighter"},
            {"name": "Minsitthar", "role": "Fighter"},
            {"name": "Terizla", "role": "Fighter"},
            {"name": "X.Borg", "role": "Fighter"},
            {"name": "Dyroth", "role": "Fighter"},
            {"name": "Masha", "role": "Fighter"},
            {"name": "Silvanna", "role": "Fighter"},
            {"name": "Yu Zhong", "role": "Fighter"},
            {"name": "Khaleed", "role": "Fighter"},
            {"name": "Barats", "role": "Fighter"},
            {"name": "Paquito", "role": "Fighter"},
            {"name": "Phoveus", "role": "Fighter"},
            {"name": "Aulus", "role": "Fighter"},
            {"name": "Fiddrin", "role": "Fighter"},
            {"name": "Arlott", "role": "Fighter"},
            {"name": "Cici", "role": "Fighter"},
            {"name": "Kaja", "role": "Fighter"},
            {"name": "Leomord", "role": "Fighter"},
            {"name": "Thamuz", "role": "Fighter"},
            {"name": "Badang", "role": "Fighter"},
            {"name": "Guinevere", "role": "Fighter"},
            # Tank
            {"name": "Alice", "role": "Tank"},
            {"name": "Tigreal", "role": "Tank"},
            {"name": "Akai", "role": "Tank"},
            {"name": "Franco", "role": "Tank"},
            {"name": "Minotaur", "role": "Tank"},
            {"name": "Lolia", "role": "Tank"},
            {"name": "Gatotkaca", "role": "Tank"},
            {"name": "Grock", "role": "Tank"},
            {"name": "Hylos", "role": "Tank"},
            {"name": "Uranus", "role": "Tank"},
            {"name": "Belerick", "role": "Tank"},
            {"name": "Khufra", "role": "Tank"},
            {"name": "Esmeralda", "role": "Tank"},
            {"name": "Terizla", "role": "Tank"},
            {"name": "Baxia", "role": "Tank"},
            {"name": "Masha", "role": "Tank"},
            {"name": "Atlas", "role": "Tank"},
            {"name": "Barats", "role": "Tank"},
            {"name": "Edith", "role": "Tank"},
            {"name": "Fredrinn", "role": "Tank"},
            {"name": "Johnson", "role": "Tank"},
            {"name": "Hilda", "role": "Tank"},
            {"name": "Carmilla", "role": "Tank"},
            {"name": "Gloo", "role": "Tank"},
            {"name": "Chip", "role": "Tank"},
            # Assassin
            {"name": "Saber", "role": "Assassin"},
            {"name": "Alucard", "role": "Assassin"},
            {"name": "Zilong", "role": "Assassin"},
            {"name": "Fanny", "role": "Assassin"},
            {"name": "Natalia", "role": "Assassin"},
            {"name": "Yi Sun-shin", "role": "Assassin"},
            {"name": "Lancelot", "role": "Assassin"},
            {"name": "Helcurt", "role": "Assassin"},
            {"name": "Lesley", "role": "Assassin"},
            {"name": "Selena", "role": "Assassin"},
            {"name": "Mathilda", "role": "Assassin"},
            {"name": "Paquito", "role": "Assassin"},
            {"name": "Yin", "role": "Assassin"},
            {"name": "Arlott", "role": "Assassin"},
            {"name": "Harley", "role": "Assassin"},
            {"name": "Suyou", "role": "Assassin"},
            # Marksman
            {"name": "Popol and Kupa", "role": "Marksman"},
            {"name": "Brody", "role": "Marksman"},
            {"name": "Beatrix", "role": "Marksman"},
            {"name": "Natan", "role": "Marksman"},
            {"name": "Melissa", "role": "Marksman"},
            {"name": "Ixia", "role": "Marksman"},
            {"name": "Hanabi", "role": "Marksman"},
            {"name": "Claude", "role": "Marksman"},
            {"name": "Kimmy", "role": "Marksman"},
            {"name": "Granger", "role": "Marksman"},
            {"name": "Wanwan", "role": "Marksman"},
            {"name": "Miya", "role": "Marksman"},
            {"name": "Bruno", "role": "Marksman"},
            {"name": "Clint", "role": "Marksman"},
            {"name": "Layla", "role": "Marksman"},
            {"name": "Yi Sun-shin", "role": "Marksman"},
            {"name": "Moskov", "role": "Marksman"},
            {"name": "Roger", "role": "Marksman"},
            {"name": "Karrie", "role": "Marksman"},
            {"name": "Irithel", "role": "Marksman"},
            {"name": "Lesley", "role": "Marksman"},
            # Mage
            {"name": "Vale", "role": "Mage"},
            {"name": "Lunox", "role": "Mage"},
            {"name": "Kadita", "role": "Mage"},
            {"name": "Cecillion", "role": "Mage"},
            {"name": "Luo Yi", "role": "Mage"},
            {"name": "Xavier", "role": "Mage"},
            {"name": "Novaria", "role": "Mage"},
            {"name": "Zhuxin", "role": "Mage"},
            {"name": "Harley", "role": "Mage"},
            {"name": "Yve", "role": "Mage"},
            {"name": "Aurora", "role": "Mage"},
            {"name": "Faramis", "role": "Mage"},
            {"name": "Esmeralda", "role": "Mage"},
            {"name": "Kagura", "role": "Mage"},
            {"name": "Cyclops", "role": "Mage"},
            {"name": "Vexana", "role": "Mage"},
            {"name": "Odette", "role": "Mage"},
            {"name": "Zhask", "role": "Mage"},
            # Support
            {"name": "Rafaela", "role": "Support"},
            {"name": "Minotaur", "role": "Support"},
            {"name": "Lolita", "role": "Support"},
            {"name": "Estes", "role": "Support"},
            {"name": "Angela", "role": "Support"},
            {"name": "Faramis", "role": "Support"},
            {"name": "Mathilda", "role": "Support"},
            {"name": "Florin", "role": "Support"},
            {"name": "Johnson", "role": "Support"},
        ]
        for char_data in characters_data:
            character = Character(name=char_data["name"], role=char_data["role"])
            session.add(character)
        session.commit()
        logger.info("Персонажі завантажені до бази даних")
    else:
        logger.info("Персонажі вже існують у базі даних")
    session.close()

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
        "Ви можете обрати персонажа за допомогою /characters.\n"
        "Якщо у вас виникнуть питання, скористайтесь /help."
    )

    keyboard = [
        ["Додати скріншот", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)

async def characters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    user_id = str(update.effective_user.id)
    characters = session.query(Character).all()

    # Отримуємо список персонажів, для яких користувач вже надіслав скріншоти
    user_screenshots = session.query(Screenshot.character_id).filter_by(user_id=user_id).all()
    user_character_ids = [sc[0] for sc in user_screenshots]

    session.close()

    # Групуємо персонажів за ролями
    roles = {}
    for char in characters:
        if char.role not in roles:
            roles[char.role] = []
        status = "✅ Отримано" if char.id in user_character_ids else "⏳ Очікується"
        button_text = f"{char.name} ({status})"
        roles[char.role].append(
            InlineKeyboardButton(button_text, callback_data=f"select_{char.name}")
        )

    keyboard = []
    for role, buttons in roles.items():
        # Додаємо кнопку з назвою ролі (не натискається)
        keyboard.append([InlineKeyboardButton(f"--- {role} ---", callback_data="ignore")])
        # Розбиваємо кнопки на рядки по 2 кнопки
        for i in range(0, len(buttons), 2):
            keyboard.append(buttons[i:i+2])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Виберіть персонажа для завантаження скріншоту:", reply_markup=reply_markup)

async def character_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ignore":
        return
    elif data.startswith("select_"):
        character_name = data.replace("select_", "")
        context.user_data['selected_character'] = character_name
        await query.edit_message_text(f"Ви вибрали: {character_name}. Будь ласка, надішліть скріншот.")

async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    session = get_session()

    user_entry = session.query(User).filter_by(user_id=user_id).first()
    if not user_entry:
        await update.message.reply_text("Ви ще не розпочали. Використайте /start для початку.")
        session.close()
        return

    if 'selected_character' not in context.user_data:
        await update.message.reply_text("Будь ласка, спочатку виберіть персонажа за допомогою /characters.")
        session.close()
        return

    character_name = context.user_data['selected_character']
    character = session.query(Character).filter_by(name=character_name).first()

    if update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()

            # Збереження скріншоту в базу даних
            screenshot = Screenshot(
                user_id=user_id,
                character_id=character.id,
                image_data=photo_bytes
            )
            session.add(screenshot)

            # Додавання внеску
            contribution = Contribution(user_id=user_id, character_id=character.id)
            session.add(contribution)

            # Перевірка на баджі
            total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()
            if total_contributions == 5 and "Початківець" not in (user_entry.badges or ""):
                add_badge(user_entry, "Початківець")
                await update.message.reply_text("Вітаємо! Ви отримали бадж **Початківець** 🎖️", parse_mode='Markdown')
            elif total_contributions == 10 and "Активний" not in (user_entry.badges or ""):
                add_badge(user_entry, "Активний")
                await update.message.reply_text("Вітаємо! Ви отримали бадж **Активний** 🎖️", parse_mode='Markdown')

            session.commit()

            await update.message.reply_text(f"Скріншот для '{character_name}' отримано та збережено! 🎉")

            # Очищаємо вибір персонажа
            context.user_data.pop('selected_character')

        except Exception as e:
            logger.error(f"Помилка при обробці скріншоту: {e}")
            await update.message.reply_text("Виникла помилка при збереженні скріншоту. Спробуйте ще раз.")
        finally:
            session.close()
    else:
        await update.message.reply_text("Будь ласка, надішліть зображення у форматі фото.")
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

    total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()

    progress_text = f"Ви завантажили {total_contributions} скріншотів."
    await update.message.reply_text(progress_text)
    session.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступні команди:\n"
        "/start - Запустити бота та отримати привітання.\n"
        "/characters - Обрати персонажа для завантаження скріншоту.\n"
        "/progress - Перевірити ваш прогрес.\n"
        "/leaderboard - Показати топ учасників.\n"
        "/help - Показати це повідомлення."
    )
    await update.message.reply_text(help_text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query == "Додати скріншот":
        await characters_command(update, context)
    elif query == "Перевірити прогрес":
        await progress_command(update, context)
    elif query in ["Команди", "Допомога"]:
        await help_command(update, context)
    else:
        await update.message.reply_text("Не зрозуміла команда. Використайте /help.")

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

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не встановлено у змінних середовища.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Створення таблиць у базі даних
    Base.metadata.create_all(bind=engine)
    # Завантаження персонажів до бази даних
    load_characters()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("characters", characters_command))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CallbackQueryHandler(character_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))
    application.add_error_handler(error_handler)

    # Запуск бота з параметром drop_pending_updates=True
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
