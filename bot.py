import os
import logging
import hashlib
import io
import matplotlib.pyplot as plt
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
from telegram.constants import ParseMode
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
    image_hash = Column(String, nullable=False)
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
    characters_data = []
    for role, characters in HEROES.items():
        for name in characters:
            characters_data.append({"name": name, "role": role})
    new_characters_added = False
    for char_data in characters_data:
        existing_char = session.query(Character).filter_by(name=char_data["name"]).first()
        if not existing_char:
            character = Character(name=char_data["name"], role=char_data["role"])
            session.add(character)
            new_characters_added = True
    if new_characters_added:
        session.commit()
        logger.info("Нові персонажі додані до бази даних")
    else:
        logger.info("Персонажі вже існують у базі даних")
    session.close()

# Ініціалізація списку персонажів
HEROES = {
    "Fighter": ["Balmond", "Alucard", "Bane", "Zilong", "Freya", "Alpha", "Ruby", "Roger", "Gatotkaca", "Jawhead", "Martis", "Aldous", "Minsitthar", "Terizla", "X.Borg", "Dyrroth", "Masha", "Silvanna", "Yu Zhong", "Khaleed", "Barats", "Paquito", "Phoveus", "Aulus", "Fredrinn", "Arlott", "Kaja", "Leomord", "Thamuz", "Badang", "Guinevere"],
    "Tank": ["Alice", "Tigreal", "Akai", "Franco", "Minotaur", "Lolita", "Gatotkaca", "Grock", "Hylos", "Uranus", "Belerick", "Khufra", "Esmeralda", "Terizla", "Baxia", "Masha", "Atlas", "Barats", "Edith", "Fredrinn", "Johnson", "Hilda", "Carmilla", "Gloo"],
    "Assassin": ["Saber", "Alucard", "Zilong", "Fanny", "Natalia", "Yi Sun-shin", "Lancelot", "Helcurt", "Lesley", "Selena", "Mathilda", "Paquito", "Yin", "Arlott", "Harley", "Gusion"],
    "Marksman": ["Popol and Kupa", "Brody", "Beatrix", "Natan", "Melissa", "Ixia", "Hanabi", "Claude", "Kimmy", "Granger", "Wanwan", "Miya", "Bruno", "Clint", "Layla", "Yi Sun-shin", "Moskov", "Roger", "Karrie", "Irithel", "Lesley"],
    "Mage": ["Vale", "Lunox", "Kadita", "Cecillion", "Luo Yi", "Xavier", "Novaria", "Zhask", "Harley", "Yve", "Aurora", "Faramis", "Esmeralda", "Kagura", "Cyclops", "Vexana", "Odette"],
    "Support": ["Rafaela", "Minotaur", "Lolita", "Estes", "Angela", "Faramis", "Mathilda", "Floryn", "Johnson"]
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
        "Оберіть потрібну опцію:"
    )
    keyboard = [
        ["Вибрати клас", "Перевірити прогрес"],
        ["Команди", "Допомога"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(reply_text, reply_markup=reply_markup)

async def choose_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")] for class_name in HEROES.keys()]
    recent_characters = context.user_data.get('recent_characters', [])
    if recent_characters:
        keyboard.append([InlineKeyboardButton("Останні персонажі", callback_data="recent_characters")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Оберіть клас персонажа, для якого хочете завантажити скріншот:",
        reply_markup=reply_markup
    )

async def handle_class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("class_"):
        selected_class = data.split("_", 1)[1]
        context.user_data['selected_class'] = selected_class
        characters = HEROES[selected_class]
        keyboard = [[InlineKeyboardButton(char, callback_data=f"character_{char}")] for char in characters]
        keyboard.append([InlineKeyboardButton("Повернутися до класів", callback_data="back_to_classes")])
        keyboard.append([InlineKeyboardButton("Повернутися до головного меню", callback_data="back_to_main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Оберіть персонажа з класу **{selected_class}**:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    elif data == "back_to_classes":
        await choose_class(update, context)

    elif data == "back_to_main_menu":
        await start(update, context)

async def handle_character_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("character_"):
        selected_character = data.split("_", 1)[1]
        context.user_data['selected_character'] = selected_character

        # Зберігаємо останні вибрані персонажі
        recent_characters = context.user_data.get('recent_characters', [])
        if selected_character not in recent_characters:
            recent_characters.insert(0, selected_character)
            if len(recent_characters) > 5:
                recent_characters.pop()
            context.user_data['recent_characters'] = recent_characters

        await query.edit_message_text(
            f"Ви вибрали: **{selected_character}**.\nБудь ласка, надішліть скріншот.",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "back_to_classes":
        await choose_class(update, context)

    elif data == "back_to_main_menu":
        await start(update, context)

    elif data == "recent_characters":
        recent_characters = context.user_data.get('recent_characters', [])
        keyboard = [[InlineKeyboardButton(char, callback_data=f"character_{char}")] for char in recent_characters]
        keyboard.append([InlineKeyboardButton("Повернутися до головного меню", callback_data="back_to_main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Оберіть одного з останніх вибраних персонажів:",
            reply_markup=reply_markup
        )

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

            # Обчислюємо хеш зображення
            image_hash = hashlib.md5(photo_bytes).hexdigest()

            # Перевіряємо на дублікати
            existing_screenshot = session.query(Screenshot).filter_by(image_hash=image_hash, user_id=user_id).first()
            if existing_screenshot:
                await update.message.reply_text("Цей скріншот вже був надісланий раніше.")
                session.close()
                return

            # Збереження скріншоту в базу даних
            screenshot = Screenshot(
                user_id=user_id,
                character_id=character.id,
                image_data=photo_bytes,
                image_hash=image_hash
            )
            session.add(screenshot)

            # Додавання внеску
            contribution = Contribution(user_id=user_id, character_id=character.id)
            session.add(contribution)

            # Перевірка на баджі
            total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()
            badges = user_entry.badges.split(", ") if user_entry.badges else []

            if total_contributions == 5 and "Початківець" not in badges:
                add_badge(user_entry, "Початківець")
                badge_image_path = 'badges/pochatkivec.png'
                await update.message.reply_photo(
                    photo=open(badge_image_path, 'rb'),
                    caption="Вітаємо! Ви отримали бадж **Початківець** 🎖️\nЗавантажте ще 5 скріншотів, щоб отримати бадж **Активний**!",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif total_contributions == 10 and "Активний" not in badges:
                add_badge(user_entry, "Активний")
                badge_image_path = 'badges/aktyvnyi.png'
                await update.message.reply_photo(
                    photo=open(badge_image_path, 'rb'),
                    caption="Вітаємо! Ви отримали бадж **Активний** 🎖️\nЗавантажте ще 10 скріншотів, щоб отримати бадж **Експерт**!",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif total_contributions == 20 and "Експерт" not in badges:
                add_badge(user_entry, "Експерт")
                badge_image_path = 'badges/ekspert.png'
                await update.message.reply_photo(
                    photo=open(badge_image_path, 'rb'),
                    caption="Вітаємо! Ви отримали бадж **Експерт** 🎖️",
                    parse_mode=ParseMode.MARKDOWN
                )

            session.commit()

            await update.message.reply_text(
                f"Скріншот для **{selected_character}** збережено! 🎉",
                parse_mode=ParseMode.MARKDOWN
            )

            # Очищуємо вибір персонажа
            context.user_data.pop('selected_character')

            # Повертаємося до головного меню
            keyboard = [
                ["Вибрати клас", "Перевірити прогрес"],
                ["Команди", "Допомога"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Повертаємося до головного меню:", reply_markup=reply_markup)

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

    if total_contributions == 0:
        await update.message.reply_text("Ви ще не завантажили жодного скріншоту.")
        session.close()
        return

    # Отримуємо дати внесків
    contributions = session.query(Contribution).filter_by(user_id=user_id).all()
    dates = [c.timestamp.date() for c in contributions]
    date_counts = {}
    for date in dates:
        date_counts[date] = date_counts.get(date, 0) + 1

    sorted_dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in sorted_dates]

    # Створюємо діаграму
    plt.figure(figsize=(10, 5))
    plt.bar(sorted_dates, counts, color='skyblue')
    plt.xlabel('Дата')
    plt.ylabel('Кількість внесків')
    plt.title('Ваша активність')
    plt.xticks(rotation=45)

    # Зберігаємо діаграму в пам'ять
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    progress_text = f"Ви завантажили **{total_contributions}** скріншотів."
    await update.message.reply_photo(
        photo=buffer,
        caption=progress_text,
        parse_mode=ParseMode.MARKDOWN
    )
    session.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступні команди:\n"
        "/start - Показати головне меню.\n"
        "/choose_class - Вибрати клас персонажа.\n"
        "/progress - Перевірити ваш прогрес.\n"
        "/help - Показати це повідомлення.\n"
        "/share - Поділитися своїм прогресом."
    )
    await update.message.reply_text(help_text)

async def share_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    session = get_session()
    total_contributions = session.query(Contribution).filter_by(user_id=user_id).count()
    session.close()

    if total_contributions == 0:
        await update.message.reply_text("Ви ще не завантажили жодного скріншоту.")
        return

    share_text = f"Я завантажив {total_contributions} скріншотів у бота Mobile Legends!"

    await update.message.reply_text(
        f"Поділіться своїми досягненнями:\n\n{share_text}"
    )

# Обробник callback запитів
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("class_") or data == "back_to_classes":
        await handle_class_selection(update, context)
    elif data.startswith("character_") or data == "recent_characters":
        await handle_character_selection(update, context)
    elif data == "back_to_main_menu":
        await start(update, context)
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

# Функція для надсилання щотижневих звітів
async def send_weekly_reports(context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    users = session.query(User).all()
    for user in users:
        total_contributions = session.query(Contribution).filter_by(user_id=user.user_id).count()
        if total_contributions > 0:
            try:
                await context.bot.send_message(
                    chat_id=int(user.user_id),
                    text=f"Привіт, {user.username}! Ви завантажили {total_contributions} скріншотів. Продовжуйте в тому ж дусі!"
                )
            except Exception as e:
                logger.error(f"Не вдалося надіслати повідомлення користувачу {user.user_id}: {e}")
    session.close()

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
    application.add_handler(CommandHandler("share", share_progress))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, add_screenshot))

    # Обробник помилок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Виникла помилка. Спробуйте пізніше.")

    application.add_error_handler(error_handler)

    # Налаштування планувальника
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_weekly_reports, 'interval', weeks=1, args=[application.bot])
    scheduler.start()

    # Запуск бота з параметром drop_pending_updates=True
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
