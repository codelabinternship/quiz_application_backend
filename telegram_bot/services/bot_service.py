import logging
from asgiref.sync import sync_to_async
from django.db import transaction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, \
    ConversationHandler

from ..models import TelegramUser
from .api_service import APIService


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, TOPIC_SELECTION, QUIZ_SELECTION = range(6)
LANGUAGE_SELECTION, PHONE_NUMBER, FULL_NAME, SUBJECT_SELECTION, TOPIC_SELECTION, QUIZ_SELECTION, QUESTION, ANSWER = range(8)


LANGUAGES = {
    "uz": "Узбекский",
    "ru": "Русский",
    "en": "Английский",
    "tr": "Турецкий",
    "ar": "Арабский",
    "ko": "Корейский"
}

QUESTION, ANSWER = range(6, 8)

TEXTS = {
    "ru": {
        "welcome": "Добро пожаловать! Пожалуйста, выберите язык:",
        "phone_request": "Пожалуйста, поделитесь своим номером телефона:",
        "share_phone": "Поделиться номером телефона",
        "name_request": "Введите ваше имя и фамилию:",
        "registration_successful": "Регистрация успешна! Теперь вы можете выбрать предмет:",
        "choose_subject": "Выберите предмет:",
        "choose_lesson": "Выберите урок:",
        "start_quiz": "Начать викторину",
        "quiz_info": "Информация о тесте:\n\nНазвание: {}\nОписание: {}\nКоличество вопросов: {}"
    },

}


for lang in LANGUAGES:
    if lang != "ru":
        TEXTS[lang] = TEXTS["ru"]


class BotService:
    def __init__(self, token):
        self.token = token
        self.application = None

    # def start(self):
    #     self.application = Application.builder().token(self.token).build()
    #
    #
    #     conv_handler = ConversationHandler(
    #         entry_points=[CommandHandler("start", self.start_command)],
    #         states={
    #             LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_handler, pattern=r"^lang_")],
    #             PHONE_NUMBER: [MessageHandler(filters.CONTACT, self.phone_handler)],
    #             FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.name_handler)],
    #             SUBJECT_SELECTION: [CallbackQueryHandler(self.subject_handler, pattern=r"^subject_")],
    #             TOPIC_SELECTION: [CallbackQueryHandler(self.topic_handler, pattern=r"^topic_")],
    #             QUIZ_SELECTION: [CallbackQueryHandler(self.quiz_handler, pattern=r"^quiz_")]
    #         },
    #         fallbacks=[CommandHandler("cancel", self.cancel_command)]
    #     )
    #
    #
    #     self.application.add_handler(conv_handler)
    #
    #
    #     self.application.run_polling()






    def start(self):
        self.application = Application.builder().token(self.token).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                LANGUAGE_SELECTION: [CallbackQueryHandler(self.language_handler, pattern=r"^lang_")],
                PHONE_NUMBER: [MessageHandler(filters.CONTACT, self.phone_handler)],
                FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.name_handler)],
                SUBJECT_SELECTION: [
                    CallbackQueryHandler(self.subject_handler, pattern=r"^subject_"),
                    CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$")
                ],
                TOPIC_SELECTION: [CallbackQueryHandler(self.topic_handler, pattern=r"^topic_")],
                QUIZ_SELECTION: [
                    CallbackQueryHandler(self.quiz_handler, pattern=r"^quiz_"),
                    CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_")
                ],
                QUESTION: [CallbackQueryHandler(self.answer_handler, pattern=r"^answer_")],
                ANSWER: [CallbackQueryHandler(self.next_question_handler, pattern=r"^next_question$")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)]
        )

        self.application.add_handler(CallbackQueryHandler(self.restart_subjects_handler, pattern=r"^restart_subjects$"))
        self.application.add_handler(CallbackQueryHandler(self.restart_quiz_handler, pattern=r"^restart_quiz_"))

        self.application.add_handler(conv_handler)
        self.application.run_polling()

    async def restart_subjects_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_subjects_sync():
                return APIService.get_subjects(language_code=lang_code)

            subjects = await get_subjects_sync()

            if not subjects:
                await query.edit_message_text("Не удалось получить список предметов. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for subject in subjects:
                keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)

            return SUBJECT_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в restart_subjects_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def next_question_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            context.user_data["current_question_index"] += 1

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в next_question_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка при переходе к следующему вопросу.")
            return ConversationHandler.END







    @staticmethod
    @transaction.atomic
    def _get_or_create_telegram_user(telegram_id, chat_id, username, first_name, last_name, language_code):
        telegram_user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'chat_id': chat_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code or 'ru'
            }
        )

        if not created:
            telegram_user.chat_id = chat_id
            telegram_user.username = username
            telegram_user.first_name = first_name
            telegram_user.last_name = last_name
            telegram_user.save()

        return telegram_user, created

    @staticmethod
    def _update_telegram_user_language(user_id, lang_code):
        telegram_user = TelegramUser.objects.get(id=user_id)
        telegram_user.language_code = lang_code
        telegram_user.save()

    @staticmethod
    def _update_telegram_user_phone(user_id, phone_number):
        telegram_user = TelegramUser.objects.get(id=user_id)
        telegram_user.phone_number = phone_number
        telegram_user.save()

    @staticmethod
    def _link_telegram_user_with_app_user(telegram_user_id, user_id):
        telegram_user = TelegramUser.objects.get(id=telegram_user_id)
        from zein_app.models import CustomUser
        telegram_user.user = CustomUser.objects.get(id=user_id)
        telegram_user.save()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.effective_user

        try:
            telegram_user, created = await sync_to_async(self._get_or_create_telegram_user)(
                telegram_id=user.id,
                chat_id=update.effective_chat.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code or 'ru'
            )


            context.user_data["telegram_user_id"] = telegram_user.id


            keyboard = []
            row = []
            for i, (lang_code, lang_name) in enumerate(LANGUAGES.items(), 1):
                button = InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")
                row.append(button)
                if i % 2 == 0:
                    keyboard.append(row)
                    row = []

            if row:
                keyboard.append(row)

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(TEXTS["ru"]["welcome"], reply_markup=reply_markup)
            return LANGUAGE_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка при запуске. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def language_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            lang_code = query.data.split("_")[1]
            context.user_data["language"] = lang_code

            telegram_user_id = context.user_data.get("telegram_user_id")
            if telegram_user_id:
                await sync_to_async(self._update_telegram_user_language)(telegram_user_id, lang_code)


            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton(text=TEXTS[lang_code]["share_phone"], request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await query.edit_message_text(text=TEXTS[lang_code]["phone_request"])
            await query.message.reply_text(
                text=TEXTS[lang_code]["phone_request"],
                reply_markup=keyboard
            )
            return PHONE_NUMBER
        except Exception as e:
            logger.error(f"Ошибка в language_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def phone_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            contact = update.message.contact
            phone_number = contact.phone_number
            context.user_data["phone"] = phone_number

            telegram_user_id = context.user_data.get("telegram_user_id")
            if telegram_user_id:
                await sync_to_async(self._update_telegram_user_phone)(telegram_user_id, phone_number)

            lang_code = context.user_data.get("language", "ru")
            await update.message.reply_text(TEXTS[lang_code]["name_request"])
            return FULL_NAME
        except Exception as e:
            logger.error(f"Ошибка в phone_handler: {e}")
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def name_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            full_name = update.message.text
            context.user_data["full_name"] = full_name

            lang_code = context.user_data.get("language", "ru")
            phone_number = context.user_data.get("phone")

            @sync_to_async
            def register_user_sync():
                return APIService.register_user(
                    phone_number=phone_number,
                    full_name=full_name,
                    language_code=lang_code
                )

            user_data = await register_user_sync()

            if user_data:
                telegram_user_id = context.user_data.get("telegram_user_id")
                if telegram_user_id:
                    await sync_to_async(self._link_telegram_user_with_app_user)(telegram_user_id, user_data["id"])

            @sync_to_async
            def get_subjects_sync():
                return APIService.get_subjects(language_code=lang_code)

            subjects = await get_subjects_sync()

            if not subjects:
                await update.message.reply_text("Не удалось получить список предметов. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for subject in subjects:
                keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(TEXTS[lang_code]["registration_successful"])
            await update.message.reply_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)
            return SUBJECT_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в name_handler: {e}")
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def subject_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            subject_id = int(query.data.split("_")[1])
            context.user_data["subject_id"] = subject_id
            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_topics_sync():
                return APIService.get_topics(subject_id, language_code=lang_code)

            topics = await get_topics_sync()

            if not topics:
                await query.edit_message_text("Не удалось получить список уроков. Попробуйте снова позже.")
                return ConversationHandler.END

            keyboard = []
            for topic in topics:
                keyboard.append([InlineKeyboardButton(topic["title"], callback_data=f"topic_{topic['id']}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(TEXTS[lang_code]["choose_lesson"], reply_markup=reply_markup)
            return TOPIC_SELECTION
        except Exception as e:
            logger.error(f"Ошибка в subject_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END



    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            quiz_data = context.user_data.get("quiz_data")
            current_index = context.user_data.get("current_question_index", 0)
            lang_code = context.user_data.get("language", "ru")

            if current_index >= len(quiz_data.get('questions', [])):
                return await self.show_quiz_results(update, context)

            question = quiz_data['questions'][current_index]

            context.user_data["current_question"] = question

            keyboard = []
            for answer in question.get('answers', []):
                callback_data = f"answer_{current_index}_{answer['id']}"
                keyboard.append([InlineKeyboardButton(answer['text'], callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)

            question_text = f"Вопрос {current_index + 1} из {context.user_data['total_questions']}:\n\n{question['text']}"

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=question_text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    text=question_text,
                    reply_markup=reply_markup
                )

            return QUESTION

        except Exception as e:
            logger.error(f"Ошибка в show_question: {e}")
            if update.callback_query:
                await update.callback_query.message.reply_text("Произошла ошибка при отображении вопроса.")
            else:
                await update.message.reply_text("Произошла ошибка при отображении вопроса.")
            return ConversationHandler.END

    # async def topic_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     try:
    #         query = update.callback_query
    #         await query.answer()
    #
    #         topic_id = int(query.data.split("_")[1])
    #         context.user_data["topic_id"] = topic_id
    #         lang_code = context.user_data.get("language", "ru")
    #
    #         @sync_to_async
    #         def get_quizzes_sync():
    #             return APIService.get_quizzes(topic_id, language_code=lang_code)
    #
    #         quizzes = await get_quizzes_sync()
    #
    #         if not quizzes or len(quizzes) == 0:
    #             await query.edit_message_text("По данной теме нет доступных тестов. Пожалуйста, выберите другую тему.")
    #             return ConversationHandler.END
    #
    #
    #         quiz = quizzes[0]
    #
    #         quiz_info = TEXTS[lang_code]["quiz_info"].format(
    #             quiz["title"],
    #             quiz["description"],
    #             quiz["questions_count"]
    #         )
    #
    #         keyboard = [[InlineKeyboardButton(TEXTS[lang_code]["start_quiz"], callback_data=f"quiz_{quiz['id']}")]]
    #         reply_markup = InlineKeyboardMarkup(keyboard)
    #
    #         await query.edit_message_text(quiz_info, reply_markup=reply_markup)
    #         return QUIZ_SELECTION
    #     except Exception as e:
    #         logger.error(f"Ошибка в topic_handler: {e}")
    #         await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    #         return ConversationHandler.END





    async def topic_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            topic_id = int(query.data.split("_")[1])
            context.user_data["topic_id"] = topic_id
            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_app_user_id():
                tg = TelegramUser.objects.get(id=context.user_data["telegram_user_id"])
                return tg.user.id

            app_user_id = await get_app_user_id()

            @sync_to_async
            def get_or_create_quiz_sync():
                return APIService.get_or_create_quiz(app_user_id, topic_id)

            quiz = await get_or_create_quiz_sync()

            if not quiz:
                await query.edit_message_text("Не удалось запустить викторину. Попробуйте позже.")
                return ConversationHandler.END


            quiz_info = TEXTS[lang_code]["quiz_info"].format(
                getattr(quiz, 'name', ''),
                getattr(quiz, 'description', ''),
                quiz.total_questions
            )
            keyboard = [
                [InlineKeyboardButton(TEXTS[lang_code]["start_quiz"], callback_data=f"quiz_{quiz.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(quiz_info, reply_markup=reply_markup)
            return QUIZ_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в topic_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END

    async def quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            quiz_id = int(query.data.split("_")[1])
            lang_code = context.user_data.get("language", "ru")
            context.user_data["quiz_id"] = quiz_id
            context.user_data["current_question_index"] = 0
            context.user_data["correct_answers"] = 0
            context.user_data["user_answers"] = {}

            @sync_to_async
            def get_quiz_with_questions_sync():
                return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)

            quiz_data = await get_quiz_with_questions_sync()

            if not quiz_data or not quiz_data.get('questions'):
                await query.edit_message_text(f"Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get('questions', []))

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в quiz_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def restart_quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            quiz_id = int(query.data.split("_")[2])
            context.user_data["quiz_id"] = quiz_id
            context.user_data["current_question_index"] = 0
            context.user_data["correct_answers"] = 0
            context.user_data["user_answers"] = {}

            lang_code = context.user_data.get("language", "ru")

            @sync_to_async
            def get_quiz_with_questions_sync():
                return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)

            quiz_data = await get_quiz_with_questions_sync()

            if not quiz_data or not quiz_data.get('questions'):
                await query.edit_message_text(f"Не удалось получить вопросы для теста.")
                return ConversationHandler.END

            context.user_data["quiz_data"] = quiz_data
            context.user_data["total_questions"] = len(quiz_data.get('questions', []))

            return await self.show_question(update, context)

        except Exception as e:
            logger.error(f"Ошибка в restart_quiz_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
            return ConversationHandler.END

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            query = update.callback_query
            await query.answer()

            _, question_index, answer_id = query.data.split("_")
            question_index = int(question_index)
            answer_id = int(answer_id)

            quiz_data = context.user_data.get("quiz_data")
            question = quiz_data['questions'][question_index]

            selected_answer = None
            is_correct = False
            for answer in question.get('answers', []):
                if answer['id'] == answer_id:
                    selected_answer = answer
                    is_correct = answer.get('is_correct', False)
                    break

            context.user_data["user_answers"][question_index] = {
                'question_id': question['id'],
                'answer_id': answer_id,
                'is_correct': is_correct
            }

            if is_correct:
                context.user_data["correct_answers"] += 1

            lang_code = context.user_data.get("language", "ru")
            if is_correct:
                result_text = "✅ Правильно!"
            else:
                correct_answer = next((a['text'] for a in question.get('answers', []) if a.get('is_correct')),
                                      "Не найдено")
                result_text = f"❌ Неправильно! Правильный ответ: {correct_answer}"

            keyboard = [[InlineKeyboardButton("Следующий вопрос", callback_data="next_question")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text=f"{question['text']}\n\nВаш ответ: {selected_answer['text']}\n\n{result_text}",
                reply_markup=reply_markup
            )

            return ANSWER

        except Exception as e:
            logger.error(f"Ошибка в answer_handler: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка при обработке ответа.")
            return ConversationHandler.END




    # async def quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     try:
    #         query = update.callback_query
    #         await query.answer()
    #
    #         quiz_id = int(query.data.split("_")[1])
    #         lang_code = context.user_data.get("language", "ru")
    #
    #
    #         @sync_to_async
    #         def get_quiz_with_questions_sync():
    #             return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)
    #
    #         quiz_data = await get_quiz_with_questions_sync()
    #
    #         if not quiz_data or not quiz_data.get('questions'):
    #             await query.edit_message_text(f"Не удалось получить вопросы для теста.")
    #             return ConversationHandler.END
    #
    #
    #         await query.edit_message_text(f"В этом месте должна быть реализована логика прохождения теста.")
    #
    #         return ConversationHandler.END
    #     except Exception as e:
    #         logger.error(f"Ошибка в quiz_handler: {e}")
    #         await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    #         return ConversationHandler.END
    #
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Операция отменена.")
        return ConversationHandler.END




# async def quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         query = update.callback_query
#         await query.answer()
#
#         quiz_id = int(query.data.split("_")[1])
#         lang_code = context.user_data.get("language", "ru")
#         context.user_data["quiz_id"] = quiz_id
#         context.user_data["current_question_index"] = 0
#         context.user_data["correct_answers"] = 0
#         context.user_data["user_answers"] = {}
#
#         @sync_to_async
#         def get_quiz_with_questions_sync():
#             return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)
#
#         quiz_data = await get_quiz_with_questions_sync()
#
#         if not quiz_data or not quiz_data.get('questions'):
#             await query.edit_message_text(f"Не удалось получить вопросы для теста.")
#             return ConversationHandler.END
#
#         context.user_data["quiz_data"] = quiz_data
#         context.user_data["total_questions"] = len(quiz_data.get('questions', []))
#
#
#         return await self.show_question(update, context)
#
#     except Exception as e:
#         logger.error(f"Ошибка в quiz_handler: {e}")
#         await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#         return ConversationHandler.END


# async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         quiz_data = context.user_data.get("quiz_data")
#         current_index = context.user_data.get("current_question_index", 0)
#         lang_code = context.user_data.get("language", "ru")
#
#
#         if current_index >= len(quiz_data.get('questions', [])):
#             return await self.show_quiz_results(update, context)
#
#         question = quiz_data['questions'][current_index]
#
#
#         context.user_data["current_question"] = question
#
#
#         keyboard = []
#         for answer in question.get('answers', []):
#             callback_data = f"answer_{current_index}_{answer['id']}"
#             keyboard.append([InlineKeyboardButton(answer['text'], callback_data=callback_data)])
#
#         reply_markup = InlineKeyboardMarkup(keyboard)
#
#
#         question_text = f"Вопрос {current_index + 1} из {context.user_data['total_questions']}:\n\n{question['text']}"
#
#         if update.callback_query:
#             await update.callback_query.edit_message_text(
#                 text=question_text,
#                 reply_markup=reply_markup
#             )
#         else:
#             await update.message.reply_text(
#                 text=question_text,
#                 reply_markup=reply_markup
#             )
#
#         return QUESTION
#
#     except Exception as e:
#         logger.error(f"Ошибка в show_question: {e}")
#         if update.callback_query:
#             await update.callback_query.message.reply_text("Произошла ошибка при отображении вопроса.")
#         else:
#             await update.message.reply_text("Произошла ошибка при отображении вопроса.")
#         return ConversationHandler.END


# async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         query = update.callback_query
#         await query.answer()
#
#
#         _, question_index, answer_id = query.data.split("_")
#         question_index = int(question_index)
#         answer_id = int(answer_id)
#
#
#         quiz_data = context.user_data.get("quiz_data")
#         question = quiz_data['questions'][question_index]
#
#
#         selected_answer = None
#         is_correct = False
#         for answer in question.get('answers', []):
#             if answer['id'] == answer_id:
#                 selected_answer = answer
#                 is_correct = answer.get('is_correct', False)
#                 break
#
#         context.user_data["user_answers"][question_index] = {
#             'question_id': question['id'],
#             'answer_id': answer_id,
#             'is_correct': is_correct
#         }
#
#         if is_correct:
#             context.user_data["correct_answers"] += 1
#
#
#         lang_code = context.user_data.get("language", "ru")
#         if is_correct:
#             result_text = "✅ Правильно!"
#         else:
#             correct_answer = next((a['text'] for a in question.get('answers', []) if a.get('is_correct')), "Не найдено")
#             result_text = f"❌ Неправильно! Правильный ответ: {correct_answer}"
#
#
#         keyboard = [[InlineKeyboardButton("Следующий вопрос", callback_data="next_question")]]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#
#         await query.edit_message_text(
#             text=f"{question['text']}\n\nВаш ответ: {selected_answer['text']}\n\n{result_text}",
#             reply_markup=reply_markup
#         )
#
#         return ANSWER
#
#     except Exception as e:
#         logger.error(f"Ошибка в answer_handler: {e}")
#         await update.callback_query.message.reply_text("Произошла ошибка при обработке ответа.")
#         return ConversationHandler.END


# async def next_question_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         query = update.callback_query
#         await query.answer()
#
#
#         context.user_data["current_question_index"] += 1
#
#
#         return await self.show_question(update, context)
#
#     except Exception as e:
#         logger.error(f"Ошибка в next_question_handler: {e}")
#         await update.callback_query.message.reply_text("Произошла ошибка при переходе к следующему вопросу.")
#         return ConversationHandler.END


async def show_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        quiz_data = context.user_data.get("quiz_data")
        correct_answers = context.user_data.get("correct_answers", 0)
        total_questions = context.user_data.get("total_questions", 0)
        lang_code = context.user_data.get("language", "ru")
        quiz_id = context.user_data.get("quiz_id")


        @sync_to_async
        def save_quiz_results_sync():
            return APIService.save_quiz_results(
                quiz_id=quiz_id,
                user_answers=context.user_data.get("user_answers", {}),
                correct_answers=correct_answers,
                total_questions=total_questions
            )

        await save_quiz_results_sync()


        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        if percentage >= 80:
            message = "Отлично! Вы отлично справились с тестом!"
        elif percentage >= 60:
            message = "Хорошо! Вы успешно прошли тест."
        else:
            message = "Вам стоит повторить материал и попробовать ещё раз."


        result_text = f"Тест завершен!\n\n" \
                      f"Правильных ответов: {correct_answers} из {total_questions}\n" \
                      f"Процент успеха: {percentage:.1f}%\n\n" \
                      f"{message}"


        keyboard = [
            [InlineKeyboardButton("Выбрать другой предмет", callback_data="restart_subjects")],
            [InlineKeyboardButton("Пройти этот тест снова", callback_data=f"restart_quiz_{quiz_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=result_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=result_text,
                reply_markup=reply_markup
            )

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка в show_quiz_results: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text("Произошла ошибка при отображении результатов.")
        else:
            await update.message.reply_text("Произошла ошибка при отображении результатов.")
        return ConversationHandler.END







# async def restart_subjects_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         query = update.callback_query
#         await query.answer()
#
#         lang_code = context.user_data.get("language", "ru")
#
#         @sync_to_async
#         def get_subjects_sync():
#             return APIService.get_subjects(language_code=lang_code)
#
#         subjects = await get_subjects_sync()
#
#         if not subjects:
#             await query.edit_message_text("Не удалось получить список предметов. Попробуйте снова позже.")
#             return ConversationHandler.END
#
#         keyboard = []
#         for subject in subjects:
#             keyboard.append([InlineKeyboardButton(subject["title"], callback_data=f"subject_{subject['id']}")])
#
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await query.edit_message_text(TEXTS[lang_code]["choose_subject"], reply_markup=reply_markup)
#
#         return SUBJECT_SELECTION
#
#     except Exception as e:
#         logger.error(f"Ошибка в restart_subjects_handler: {e}")
#         await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#         return ConversationHandler.END


# async def restart_quiz_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     try:
#         query = update.callback_query
#         await query.answer()
#
#         quiz_id = int(query.data.split("_")[2])
#         context.user_data["quiz_id"] = quiz_id
#         context.user_data["current_question_index"] = 0
#         context.user_data["correct_answers"] = 0
#         context.user_data["user_answers"] = {}
#
#
#         lang_code = context.user_data.get("language", "ru")
#
#         @sync_to_async
#         def get_quiz_with_questions_sync():
#             return APIService.get_quiz_with_questions(quiz_id, language_code=lang_code)
#
#         quiz_data = await get_quiz_with_questions_sync()
#
#         if not quiz_data or not quiz_data.get('questions'):
#             await query.edit_message_text(f"Не удалось получить вопросы для теста.")
#             return ConversationHandler.END
#
#         context.user_data["quiz_data"] = quiz_data
#         context.user_data["total_questions"] = len(quiz_data.get('questions', []))
#
#
#         return await self.show_question(update, context)
#
#     except Exception as e:
#         logger.error(f"Ошибка в restart_quiz_handler: {e}")
#         await update.callback_query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
#         return ConversationHandler.END