import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

# Імена учасників і їхні привітання
users = {
    "@anwesxx": "Привіт, Анна! Дякуємо за твою допомогу!",
    "@Undertaker_A": "Михайло, вітаємо! Твоя підтримка безцінна!",
    "@Konnerpo": "Артем, ти незамінний учасник команди!",
    "@chaos_queen_fs": "Монорочка, твоя допомога неоціненна!",
    "@Lyoha221": "Льоха, дякуємо за твої зусилля!",
    "@PeachBombastic": "Peach, ти чудовий помічник!",
    "@Kvas_Enjoyer": "Квасовий поціновувач, дякуємо за твою допомогу!",
    "@HOMYARCHOK": "Хом'як, ти справжній друг команди!",
    "@lilTitanlil": "Малий Титан, твоя участь важлива!",
    "@Crysun": "Кріс, твоя допомога просто незамінна!",
    "@is_mlbb": "Олег, ти наш лідер та головний натхненник!"
}

# Клавіатура для команд
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        ['Додати скріншот', 'Перевірити прогрес'],
        ['Команди', 'Допомога']
    ], resize_keyboard=True)

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.username
    greeting = users.get(f"@{user_id}", "Привіт! Дякуємо за допомогу!")
    update.message.reply_text(greeting, reply_markup=get_main_keyboard())

def add_screenshot(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Надішліть скріншот, і ми його збережемо.")

def check_progress(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Ваш прогрес у збереженні скріншотів: [інформація тут]")

def main():
    # Отримання токену з середовища
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_screenshot", add_screenshot))
    dp.add_handler(CommandHandler("check_progress", check_progress))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
