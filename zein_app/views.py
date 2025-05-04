from django.shortcuts import render
from rest_framework import viewsets
from .pagination import CustomPagination
from rest_framework import filters


# Create your views here.


from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
# from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken


from django.contrib.auth import get_user_model
User = get_user_model()



from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated



class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            access_token = AccessToken.for_user(user)
            return Response({
                'access': str(access_token),
                'user': UserSerializer(user).data
            })
            # refresh = RefreshToken.for_user(user)
            # user_serializer = UserSerializer(user)
            # return Response({
            #     'refresh': str(refresh),
            #     'access': str(refresh.access_token),
            #     'user': user_serializer.data
            # })
        else:
            return Response({'detail': "Invalid credentials"}, status=401)


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_serializer = UserSerializer(user)
        return Response({
            'message': 'Welcome to dashboard!',
            'user': user_serializer.data
        }, 200)


















from .models import (
    CustomUser, BadPassword, History, Subject, Topic,
    Question, UserAnswer, Course, Teacher, FAQ, Contact
)
from .serializers import (
    CustomUserSerializer, BadPasswordSerializer, HistorySerializer,
    QuestionSerializer, UserAnswerSerializer,
    CourseSerializer, TeacherSerializer, FAQSerializer, ContactSerializer
)



class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['username', 'created_at']
    ordering = ['username']



class BadPasswordViewSet(viewsets.ModelViewSet):
    queryset = BadPassword.objects.all()
    serializer_class = BadPasswordSerializer



# class QuestionViewSet(viewsets.ModelViewSet):
#     queryset = Question.objects.all()
#     serializer_class = QuestionSerializer
#     pagination_class = CustomPagination
#     filter_backends = [filters.OrderingFilter]
#     ordering_fields = ['created_at', 'text']
#     ordering = ['-created_at']



class HistoryViewSet(viewsets.ModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer



# class SubjectViewSet(viewsets.ModelViewSet):
#     queryset = Subject.objects.all()
#     serializer_class = SubjectSerializer
#     pagination_class = CustomPagination
#     filter_backends = [filters.OrderingFilter]
#     ordering_fields = ['name_en', 'name_uz']
#     ordering = ['name_en']



# class TopicViewSet(viewsets.ModelViewSet):
#     queryset = Topic.objects.all()
#     serializer_class = TopicSerializer



# class QuizSessionViewSet(viewsets.ModelViewSet):
#     queryset = QuizSession.objects.all()
#     serializer_class = QuizSessionSerializer



# class UserAnswerViewSet(viewsets.ModelViewSet):
#     queryset = UserAnswer.objects.all()
#     serializer_class = UserAnswerSerializer


from rest_framework.decorators import api_view
from .models import Question, Choice

@api_view(['POST'])
def submit_answer(request, pk):
    try:
        question = Question.objects.get(pk=pk)
        choice_id = request.data.get('choice_id')
        selected_choice = Choice.objects.get(id=choice_id, question=question)

        is_correct = selected_choice.is_correct
        return Response({
            "question": question.text,
            "your_answer": selected_choice.text,
            "correct": is_correct
        })
    except (Question.DoesNotExist, Choice.DoesNotExist):
        return Response({"error": "Invalid question or choice"}, status=400)







from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response


from .models import Subject, Topic, Question, Choice, Quiz, UserAnswer
from .serializers import (
    SubjectListSerializer, SubjectDetailSerializer,
    TopicListSerializer, TopicDetailSerializer,
    QuestionListSerializer, QuestionDetailSerializer, AdminQuestionSerializer,
    QuizCreateSerializer, QuizAnswerSerializer, QuizResultSerializer, QuizDetailSerializer
)
from .permissions import IsAdminOrReadOnly


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return SubjectListSerializer
        return SubjectDetailSerializer


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return TopicListSerializer
        return TopicDetailSerializer

    def get_queryset(self):
        queryset = Topic.objects.all()
        subject_id = self.request.query_params.get('subject_id', None)
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminQuestionSerializer
        if self.action == 'list':
            return QuestionListSerializer
        return QuestionDetailSerializer

    def get_queryset(self):
        queryset = Question.objects.all()
        topic_id = self.request.query_params.get('topic_id', None)
        if topic_id is not None:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset


class QuizAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        if serializer.is_valid():
            topic_id = serializer.validated_data['topic'].id

            questions = Question.objects.filter(topic_id=topic_id)

            if not questions.exists():
                return Response(
                    {"error": "В данной теме нет вопросов"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            quiz = Quiz.objects.create(
                user=request.user,
                topic_id=topic_id,
                total_questions=questions.count()
            )

            first_question = questions.first()
            question_serializer = QuestionDetailSerializer(first_question)

            return Response({
                "quiz_id": quiz.id,
                "question": question_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def next_question(self, request, quiz_id):
        """Получение следующего вопроса викторины"""
        quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)

        if quiz.status == 'completed':
            return Response(
                {"error": "Эта викторина уже завершена", "quiz_id": quiz.id},
                status=status.HTTP_400_BAD_REQUEST
            )

        all_questions = Question.objects.filter(topic=quiz.topic)

        answered_question_ids = UserAnswer.objects.filter(quiz=quiz).values_list('question_id', flat=True)

        next_question = all_questions.exclude(id__in=answered_question_ids).first()

        if next_question:
            question_serializer = QuestionDetailSerializer(next_question)
            return Response({
                "quiz_id": quiz.id,
                "question": question_serializer.data
            })
        else:
            quiz.status = 'completed'
            quiz.completed_at = timezone.now()
            quiz.save()

            result_serializer = QuizResultSerializer(quiz)
            return Response({
                "message": "Викторина завершена",
                "results": result_serializer.data
            })

    @action(detail=True, methods=['post'])
    def answer(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)

        if quiz.status == 'completed':
            return Response(
                {"error": "Эта викторина уже завершена"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = QuizAnswerSerializer(data=request.data)
        if serializer.is_valid():
            question_id = serializer.validated_data['question_id']
            choice_id = serializer.validated_data['choice_id']

            question = get_object_or_404(Question, id=question_id, topic=quiz.topic)

            choice = get_object_or_404(Choice, id=choice_id, question=question)

            if UserAnswer.objects.filter(quiz=quiz, question=question).exists():
                return Response(
                    {"error": "Вы уже ответили на этот вопрос"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            is_correct = choice.is_correct
            UserAnswer.objects.create(
                quiz=quiz,
                question=question,
                selected_choice=choice,
                is_correct=is_correct
            )

            if is_correct:
                quiz.score += 1
                quiz.save()

            all_questions = Question.objects.filter(topic=quiz.topic)

            answered_question_ids = UserAnswer.objects.filter(quiz=quiz).values_list('question_id', flat=True)

            if all_questions.count() == len(answered_question_ids):
                quiz.status = 'completed'
                quiz.completed_at = timezone.now()
                quiz.save()

                result_serializer = QuizResultSerializer(quiz)
                return Response({
                    "message": "Викторина завершена",
                    "is_correct": is_correct,
                    "results": result_serializer.data
                })
            else:
                next_question = all_questions.exclude(id__in=answered_question_ids).first()
                question_serializer = QuestionDetailSerializer(next_question)

                return Response({
                    "is_correct": is_correct,
                    "next_question": question_serializer.data
                })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, quiz_id=None):
        user = request.user

        if quiz_id:
            quiz = get_object_or_404(Quiz, id=quiz_id, user=user)
            serializer = QuizDetailSerializer(quiz)
            return Response(serializer.data)
        else:
            quizzes = Quiz.objects.filter(user=user)
            serializer = QuizResultSerializer(quizzes, many=True)
            return Response(serializer.data)













class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer



class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer



class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer



class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


# views.py
from rest_framework import viewsets
from .models import TelegramBot
from .serializers import TelegramBotSerializer

class TelegramBotViewSet(viewsets.ModelViewSet):
    queryset = TelegramBot.objects.all()
    serializer_class = TelegramBotSerializer
