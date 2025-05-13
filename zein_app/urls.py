from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from .views import TelegramBotViewSet

from .views import (
    CustomUserViewSet, BadPasswordViewSet, HistoryViewSet, CourseViewSet, TeacherViewSet, FAQViewSet, ContactViewSet
)
from .views import RequestCreateAPIView, RequestDetailAPIView

from .views import submit_answer

from .views import SubjectViewSet, TopicViewSet, QuestionViewSet, QuizAPIView
from .views import ResultsViewSet
router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'questions', QuestionViewSet)

router.register(r'history', HistoryViewSet)
# router.register(r'questions', QuestionViewSet)
router.register(r'users', CustomUserViewSet)
router.register(r'bad-passwords', BadPasswordViewSet)
# router.register(r'subjects', SubjectViewSet)
# router.register(r'topics', TopicViewSet)
# router.register(r'quiz-sessions', QuizSessionViewSet)
# router.register(r'user-answers', UserAnswerViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'bots', TelegramBotViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'results', ResultsViewSet)


urlpatterns = [
    path('', include(router.urls)),

    path('quiz/', QuizAPIView.as_view(), name='quiz-create'),
    path('quiz/<int:quiz_id>/', QuizAPIView.as_view(), name='quiz-detail'),
    path('quiz/<int:quiz_id>/next/', QuizAPIView.next_question, name='quiz-next-question'),
    path('quiz/<int:quiz_id>/answer/', QuizAPIView.answer, name='quiz-answer'),
    path('questions/<int:pk>/submit/', submit_answer, name='submit-answer'),
    path('requests/', RequestCreateAPIView.as_view(), name='request-create'),
    path('requests/<int:pk>/', RequestDetailAPIView.as_view(), name='request-delete'),
    path('results/language/<str:language>/', ResultsViewSet.as_view({'get': 'by_language'}), name='results-by-language'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




