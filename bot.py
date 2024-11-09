import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, LargeBinary, Table
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

# Визначення асоціативної таблиці для багато-до-багатьох зв’язку між користувачами та тегами
user_tags = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.user_id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Моделі бази даних
class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    badges = Column(String, default="")
    tags = relationship("Tag", secondary=user_tags, back_populates="users")
    contributions = relationship("Contribution", back_populates="user")
    screenshots = relationship("Screenshot", back_populates="user")

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary=user_tags, back_populates="tags")

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
            # Tank
            {"name": "Alice", "role": "Tank"},
            {"name": "Tigreal", "role": "Tank"},
            {"name": "Akai", "role": "Tank"},
            {"name": "Franco", "role": "Tank"},
            {"name": "Minotaur", "role": "Tank"},
            # Assassin
            {"name": "Saber", "role": "Assassin"},
            {"name": "Alucard", "role": "Assassin"},
            {"name": "Zilong", "role": "Assassin"},
            {"name": "Fanny", "role": "Assassin"},
            {"name": "Natalia", "role": "Assassin"},
            # Marksman
            {"name": "Popol and Kupa", "role": "Marksman"},
            {"name": "Brody", "role": "Marksman"},
            {"name": "Beatrix", "role": "Marksman"},
            {"name": "Natan", "role": "Marksman"},
            {"name": "Melissa", "role": "Marksman"},
            # Mage
            {"name": "Vale", "role": "Mage"},
            {"name": "Lunox", "role": "Mage"},
            {"name": "Kadita", "role": "Mage"},
            {"name": "Cecillion", "role": "Mage"},
            {"name": "Luo Yi", "role": "Mage"},
            # Support
            {"name": "Rafaela", "role": "Support"},
            {"name": "Minotaur", "role": "Support"},
            {"name": "Lolita", "role": "Support"},
            {"name": "Estes", "role": "Support"},
            {"name": "Angela", "role": "Support"},
        ]
        for char_data in characters_data:
            # Перевірка на унікальність імені персонажа
            existing_char = session.query(Character).filter_by(name=char_data["name"]).first()
            if not existing_char:
                character = Character(name=char_data["name"], role=char_data["role"])
                session.add(character)
        session.commit()
        logger.info("Персонажі завантажені до бази даних")
    else:
        logger.info("Персонажі вже існують у базі даних")
    session.close()

# Ініціалізація списку персонажів
HEROES = {
    "Fighter": ["Balmond", "Alucard", "Bane", "Zilong", "Freya"],
    "Tank": ["Alice", "Tigreal", "Akai", "Franco", "Minotaur"],
    "Assassin": ["Saber", "Alucard", "Zilong", "Fanny", "Natalia"],
    "Marksman": ["Popol and Kupa", "Brody", "Beatrix", "Natan", "Melissa"],
    "Mage": ["Vale", "Lunox", "Kadita", "Cecillion", "Luo Yi"],
    "Support": ["Rafaela", "Minotaur", "Lolita", "Estes", "Angela"],
}

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
        "Ласкаво просимо до нашого бота. Ось доступні опції:"
    )
    keyboard = [
        ["Вибрати клас", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)

async def choose_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")] for class_name in HEROES.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть клас персонажа:", reply_markup=reply_markup)

async def handle_class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("class_"):
        selected_class = data.split("_")[1]
        context.user_data['selected_class'] = selected_class
        characters = HEROES[selected_class]
        keyboard = [[InlineKeyboardButton(char, callback_data=f"character_{char}")] for char in characters]
        keyboard.append([InlineKeyboardButton("Повернутися до класів", callback_data="back_to_classes")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Оберіть персонажа з класу **{selected_class}**:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "back_to_classes":
        keyboard = [[InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")] for class_name in HEROES.keys()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Оберіть клас персонажа:", reply_markup=reply_markup)

async def handle_character_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("character_"):
        selected_character = data.split("_")[1]
        context.user_data['selected_character'] = selected_character
        await query.edit_message_text(
            f"Ви вибрали: **{selected_character}**.\nБудь ласка, надішліть скріншот.",
            parse_mode='Markdown'
        )

    elif data == "back_to_classes":
        keyboard = [[InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")] for class_name in HEROES.keys()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Оберіть клас персонажа:", reply_markup=reply_markup)

async def add_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    session = get_session()

    user_entry = session.query(User).filter_by(user_id=user_id).first()
    if not user_entry:
        await update.message.reply_text("Ви ще не зареєстровані. Використайте /start для реєстрації.")
        session.close()
        return

    if 'selected_character' not in context.user_data:
        await update.message.reply_text("Будь ласка, спочатку оберіть персонажа за допомогою кнопок меню.")
        session.close()
        return

    selected_character = context.user_data['selected_character']
    character = session.query(Character).filter_by(name=selected_character).first()

    if not character:
        await update.message.reply_text("Вибраний персонаж не знайдений у базі даних.")
        session.close()
        return

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

            await update.message.reply_text(
                f"Скріншот для **{selected_character}** отримано та збережено! 🎉",
                parse_mode='Markdown'
            )

            # Очищуємо вибір персонажа
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
        await update.message.reply_text("Ви ще не зареєстровані. Використайте /start для реєстрації.")
        session.close()
        return

    total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()

    progress_text = f"Ви завантажили **{total_contributions}** скріншотів."
    await update.message.reply_text(progress_text, parse_mode='Markdown')
    session.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступні команди:\n"
        "/start - Показати головне меню.\n"
        "/choose_class - Вибрати клас персонажа.\n"
        "/progress - Перевірити ваш прогрес.\n"
        "/help - Показати це повідомлення."
    )
    await update.message.reply_text(help_text)

# Обробник callback запитів
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("class_"):
        await handle_class_selection(update, context)
    elif data.startswith("character_"):
        await handle_character_selection(update, context)
    elif data == "back_to_classes":
        await handle_class_selection(update, context)
    else:
        await query.answer("Не зрозумілий вибір.")

# Обробник повідомлень для кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Вибрати клас":
        await choose_class(update, context)
    elif text == "Перевірити прогрес":
        await progress_command(update, context)
    elif text == "Команди":
        await help_command(update, context)
    elif text == "Допомога":
        await help_command(update, context)
    else:
        await update.message.reply_text("Не зрозуміла команда. Використайте /help.")

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
    application.add_handler(CommandHandler("choose_class", choose_class))
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))

    # Обробник помилок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Виникла помилка. Спробуйте пізніше.")

    application.add_error_handler(error_handler)

    # Запуск бота з параметром drop_pending_updates=True
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
