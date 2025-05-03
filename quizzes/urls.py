from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, UserQuizAttemptListView

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path('', include(router.urls)),
    path('my-attempts/', UserQuizAttemptListView.as_view(), name='my-attempts'),
]