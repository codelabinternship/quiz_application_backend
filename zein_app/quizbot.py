# from aiogram import Bot, Dispatcher, types
# from aiogram.utils import executor
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
# API_TOKEN = os.getenv("BOT_TOKEN")
#
# bot = Bot(token=API_TOKEN)
# dp = Dispatcher(bot)
#
# @dp.message_handler(commands=['start'])
# async def send_welcome(message: types.Message):
#     await message.reply("Assalomu alaykum! Quiz botga xush kelibsiz.")
#
# # boshqa handlerlar...
#
# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=True)


"""
Telegram бот для Quiz Application
Этот бот интегрируется с Django REST API и предоставляет пользовательский интерфейс
для выбора языка, регистрации и взаимодействия с предметами/уроками/тестами.
"""

import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, \
    ConversationHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# API адрес (измените на свой)
API_BASE_URL = "http://localhost:8000/api"

# Состояния для разговора
LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, LESSON_SELECTION, QUIZ_SELECTION = range(6)

# Доступные языки
LANGUAGES = {
    "uz": "Узбекский",
    "ru": "Русский",
    "en": "Английский",
    "tr": "Турецкий",
    "ar": "Арабский",
    "ko": "Корейский"
}

# Тексты для русского языка
TEXTS_RU = {
    "welcome": "Добро пожаловать! Пожалуйста, выберите язык:",
    "phone_request": "Пожалуйста, поделитесь своим номером телефона:",
    "name_request": "Введите ваше имя и фамилию:",
    "registration_successful": "Регистрация успешна! Теперь вы можете выбрать предмет:",
    "choose_subject": "Выберите предмет:",
    "choose_lesson": "Выберите урок:",
    "start_quiz": "Начать викторину",
    "quiz_info": "Информация о тесте:\n\nНазвание: {}\nОписание: {}\nКоличество вопросов: {}"
}


# Функция для запроса к API
async def api_request(method, endpoint, data=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}/{endpoint}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return None


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Создаем клавиатуру выбора языка
    keyboard = []
    row = []
    for i, (lang_code, lang_name) in enumerate(LANGUAGES.items(), 1):
        button = InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")
        row.append(button)
        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS_RU["welcome"], reply_markup=reply_markup)
    return LANGUAGE_SELECTION


# Обработчик выбора языка
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_")[1]
    context.user_data["language"] = lang_code

    # Для демонстрации используем только русский язык
    # Тут можно было бы загрузить соответствующие фразы для выбранного языка

    # Запрашиваем номер телефона с помощью клавиатуры
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Поделиться номером телефона", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await query.edit_message_text(text=TEXTS_RU["phone_request"])
    await query.message.reply_text(
        text="Нажмите на кнопку ниже, чтобы поделиться своим номером телефона:",
        reply_markup=keyboard
    )
    return PHONE_NUMBER


# Обработчик получения номера телефона
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    context.user_data["phone"] = contact.phone_number

    await update.message.reply_text(TEXTS_RU["name_request"])
    return FULL_NAME


# Обработчик получения имени и фамилии
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    full_name = update.message.text
    context.user_data["full_name"] = full_name

    # Здесь можно выполнить регистрацию пользователя в API
    # Пример:
    user_data = {
        "phone": context.user_data["phone"],
        "full_name": context.user_data["full_name"],
        "language": context.user_data["language"]
    }

    # Для демонстрации пропустим реальный запрос к API
    # user_response = await api_request("POST", "users/register/", data=user_data)
    # if user_response and user_response.get("token"):
    #     context.user_data["token"] = user_response["token"]

    # Получаем список предметов
    subjects = await get_subjects()
    if not subjects:
        await update.message.reply_text("Не удалось получить список предметов. Попробуйте снова позже.")
        return ConversationHandler.END

    # Создаем клавиатуру с предметами
    keyboard = []
    for subject in subjects:
        keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS_RU["registration_successful"])
    await update.message.reply_text(TEXTS_RU["choose_subject"], reply_markup=reply_markup)
    return SUBJECT_SELECTION


# Получение списка предметов (эмуляция для демонстрации)
async def get_subjects():
    # В реальном случае здесь был бы запрос к API
    # return await api_request("GET", "subject/")

    # Для демонстрации используем моковые данные
    return [
        {"id": 1, "title": "Математика"},
        {"id": 2, "title": "Информатика"},
        {"id": 3, "title": "Физика"},
        {"id": 4, "title": "Биология"}
    ]


# Получение списка уроков по предмету (эмуляция для демонстрации)
async def get_lessons(subject_id):
    # В реальном случае здесь был бы запрос к API
    # return await api_request("GET", f"lessons/?subject_id={subject_id}")

    # Для демонстрации используем моковые данные
    lessons = {
        1: [
            {"id": 101, "title": "Алгебра"},
            {"id": 102, "title": "Геометрия"},
            {"id": 103, "title": "Тригонометрия"}
        ],
        2: [
            {"id": 201, "title": "Алгоритмы"},
            {"id": 202, "title": "Базы данных"},
            {"id": 203, "title": "Программирование"}
        ],
        3: [
            {"id": 301, "title": "Механика"},
            {"id": 302, "title": "Электричество"},
            {"id": 303, "title": "Оптика"}
        ],
        4: [
            {"id": 401, "title": "Анатомия"},
            {"id": 402, "title": "Генетика"},
            {"id": 403, "title": "Экология"}
        ]
    }
    return lessons.get(subject_id, [])


# Получение информации о тесте по уроку (эмуляция для демонстрации)
async def get_quiz(lesson_id):
    # В реальном случае здесь был бы запрос к API
    # return await api_request("GET", f"quizzes/?lesson_id={lesson_id}")

    # Для демонстрации используем моковые данные
    quizzes = {
        101: {"id": 1001, "title": "Тест по алгебре", "description": "Основы алгебры", "questions_count": 10},
        102: {"id": 1002, "title": "Тест по геометрии", "description": "Основы геометрии", "questions_count": 8},
        103: {"id": 1003, "title": "Тест по тригонометрии", "description": "Основы тригонометрии",
              "questions_count": 12},
        201: {"id": 2001, "title": "Тест по алгоритмам", "description": "Основы алгоритмов", "questions_count": 15},
        202: {"id": 2002, "title": "Тест по базам данных", "description": "Основы БД", "questions_count": 10},
        203: {"id": 2003, "title": "Тест по программированию", "description": "Основы программирования",
              "questions_count": 20},
        301: {"id": 3001, "title": "Тест по механике", "description": "Основы механики", "questions_count": 10},
        302: {"id": 3002, "title": "Тест по электричеству", "description": "Основы электричества",
              "questions_count": 15},
        303: {"id": 3003, "title": "Тест по оптике", "description": "Основы оптики", "questions_count": 8},
        401: {"id": 4001, "title": "Тест по анатомии", "description": "Основы анатомии", "questions_count": 12},
        402: {"id": 4002, "title": "Тест по генетике", "description": "Основы генетики", "questions_count": 10},
        403: {"id": 4003, "title": "Тест по экологии", "description": "Основы экологии", "questions_count": 8}
    }
    return quizzes.get(lesson_id)


# Обработчик выбора предмета
async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    subject_id = int(query.data.split("_")[1])
    context.user_data["subject_id"] = subject_id

    # Получаем список уроков по выбранному предмету
    lessons = await get_lessons(subject_id)
    if not lessons:
        await query.edit_message_text("Не удалось получить список уроков. Попробуйте снова позже.")
        return ConversationHandler.END

    # Создаем клавиатуру с уроками
    keyboard = []
    for lesson in lessons:
        keyboard.append([InlineKeyboardButton(lesson["title"], callback_data=f"lesson_{lesson['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(TEXTS_RU["choose_lesson"], reply_markup=reply_markup)
    return LESSON_SELECTION


# Обработчик выбора урока
async def lesson_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    lesson_id = int(query.data.split("_")[1])
    context.user_data["lesson_id"] = lesson_id

    # Получаем информацию о тесте по выбранному уроку
    quiz = await get_quiz(lesson_id)
    if not quiz:
        await query.edit_message_text("Не удалось получить информацию о тесте. Попробуйте снова позже.")
        return ConversationHandler.END

    # Создаем сообщение с информацией о тесте и кнопкой для начала
    quiz_info = TEXTS_RU["quiz_info"].format(
        quiz["title"],
        quiz["description"],
        quiz["questions_count"]
    )

    keyboard = [[InlineKeyboardButton(TEXTS_RU["start_quiz"], callback_data=f"quiz_{quiz['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(quiz_info, reply_markup=reply_markup)
    return QUIZ_SELECTION


# Обработчик выбора теста
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    quiz_id = int(query.data.split("_")[1])

    # Тут бы начиналась логика прохождения теста, но для демонстрации просто выведем сообщение
    await query.edit_message_text(f"Вы начали проходить тест с ID: {quiz_id}.\n\n"
                                  f"В реальном приложении здесь бы начался процесс прохождения теста с отображением вопросов и вариантов ответов.")

    return ConversationHandler.END


# Обработчик отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


def main() -> None:
    # Создаем приложение Telegram бота
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE_SELECTION: [CallbackQueryHandler(language_handler, pattern=r"^lang_")],
            PHONE_NUMBER: [MessageHandler(filters.CONTACT, phone_handler)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            SUBJECT_SELECTION: [CallbackQueryHandler(subject_handler, pattern=r"^subject_")],
            LESSON_SELECTION: [CallbackQueryHandler(lesson_handler, pattern=r"^lesson_")],
            QUIZ_SELECTION: [CallbackQueryHandler(quiz_handler, pattern=r"^quiz_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()