from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from .views import TelegramBotViewSet

from .views import (
    CustomUserViewSet, BadPasswordViewSet, HistoryViewSet,
    SubjectViewSet, TopicViewSet, QuestionViewSet, QuizSessionViewSet,
    UserAnswerViewSet, CourseViewSet, TeacherViewSet, FAQViewSet, ContactViewSet
)

router = DefaultRouter()
router.register(r'history', HistoryViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'users', CustomUserViewSet)
router.register(r'bad-passwords', BadPasswordViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'quiz-sessions', QuizSessionViewSet)
router.register(r'user-answers', UserAnswerViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'faq', FAQViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'bots', TelegramBotViewSet)

urlpatterns = [
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)