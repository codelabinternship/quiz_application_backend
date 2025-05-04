from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Quiz, Question, Option, UserAnswer, QuizAttempt
from .serializers import (
    QuizSerializer, QuizListSerializer, UserAnswerSerializer,
    AnswerSubmissionSerializer, QuizResultSerializer, QuizAttemptSerializer
)


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return QuizListSerializer
        return QuizSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        quiz = self.get_object()

        serializer = AnswerSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data['quiz_id'] != int(pk):
            return Response(
                {"detail": "ID викторины в URL не соответствует quiz_id в данных запроса"},
                status=status.HTTP_400_BAD_REQUEST
            )

        answers = serializer.validated_data['answers']


        question_ids = [answer['question_id'] for answer in answers]
        quiz_question_ids = quiz.questions.values_list('id', flat=True)

        invalid_questions = set(question_ids) - set(quiz_question_ids)
        if invalid_questions:
            return Response(
                {"detail": f"Вопросы с ID {invalid_questions} не принадлежат этой викторине"},
                status=status.HTTP_400_BAD_REQUEST
            )

        for answer in answers:
            question = get_object_or_404(Question, id=answer['question_id'])
            option_ids = question.options.values_list('id', flat=True)

            if answer['option_id'] not in option_ids:
                return Response(
                    {"detail": f"Вариант {answer['option_id']} не принадлежит вопросу {answer['question_id']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        with transaction.atomic():
            UserAnswer.objects.filter(user=request.user, question__quiz=quiz).delete()

            for answer in answers:
                question = Question.objects.get(id=answer['question_id'])
                option = Option.objects.get(id=answer['option_id'])

                UserAnswer.objects.create(
                    user=request.user,
                    question=question,
                    selected_option=option
                )
            score_data = quiz.get_score(request.user)
            QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                score=score_data['percentage']
            )
        return Response({
            "message": "Ответы успешно отправлены",
            "score": score_data
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def result(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizResultSerializer(quiz, context={'user': request.user})
        return Response(serializer.data)


class UserQuizAttemptListView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)