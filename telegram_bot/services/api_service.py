import requests
import logging
from django.conf import settings
# from account.models import User
from zein_app.models import Subject, Topic, CustomUser
from zein_app.models import Quiz, Question, UserAnswer

logger = logging.getLogger(__name__)


class APIService:
    @staticmethod
    def get_subjects(language_code='ru'):
        try:
            subjects = Subject.objects.all()
            # subjects = Subject.objects.filter(is_active=True)
            return [
                {
                    'id': subject.id,
                    'title': subject.name,
                    # 'title': subject.title_ru if language_code == 'ru' else subject.title,
                    'description': subject.description
                }
                for subject in subjects
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении предметов: {e}")
            return []

    @staticmethod
    def get_topics(subject_id, language_code='ru'):
        try:
            topics = Topic.objects.filter(subject_id=subject_id, is_active=True)
            return [
                {
                    'id': topic.id,
                    # 'title': topic.title_ru if language_code == 'ru' else topic.title,
                    'title': topic.name,
                    'description': topic.description
                }
                for topic in topics
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении тем для предмета {subject_id}: {e}")
            return []

    @staticmethod
    def get_quizzes(topic_id, language_code='ru'):
        try:
            quizzes = Quiz.objects.filter(topic_id=topic_id, is_active=True)
            return [
                {
                    'id': quiz.id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'questions_count': quiz.questions.count()
                }
                for quiz in quizzes
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении тестов для темы {topic_id}: {e}")
            return []

    @staticmethod
    def get_quiz_with_questions(quiz_id, language_code='ru'):
        try:
            quiz = Quiz.objects.get(id=quiz_id, is_active=True)
            questions = Question.objects.filter(quiz=quiz, is_active=True)

            quiz_data = {
                'id': quiz.id,
                'title': quiz.name,
                # 'title': quiz.title_ru if language_code == 'ru' else quiz.title,
                'description': quiz.description,
                'questions': []
            }

            for question in questions:
                answers = UserAnswer.objects.filter(question=question)
                question_data = {
                    'id': question.id,
                    'text': question.text,
                    'answers': [
                        {
                            'id': answer.id,
                            'text': answer.text,
                            'is_correct': answer.is_correct
                        }
                        for answer in answers
                    ]
                }
                quiz_data['questions'].append(question_data)

            return quiz_data
        except Quiz.DoesNotExist:
            logger.warning(f"Тест с ID {quiz_id} не найден")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении теста с ID {quiz_id}: {e}")
            return None

    @staticmethod
    def register_user(phone_number, full_name, language_code='ru'):
        try:
            names = full_name.split(maxsplit=1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ""

            user, created = CustomUser.objects.get_or_create(
                phone=phone_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    # 'language': language_code,
                    'username': phone_number
                }
            )

            return {
                'id': user.id,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created': created
            }
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя: {e}")
            return None