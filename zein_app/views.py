from django.shortcuts import render
from rest_framework import viewsets


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
    Question, QuizSession, UserAnswer, Course, Teacher, FAQ, Contact
)
from .serializers import (
    CustomUserSerializer, BadPasswordSerializer, HistorySerializer, SubjectSerializer,
    TopicSerializer, QuestionSerializer, QuizSessionSerializer, UserAnswerSerializer,
    CourseSerializer, TeacherSerializer, FAQSerializer, ContactSerializer
)



class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer



class BadPasswordViewSet(viewsets.ModelViewSet):
    queryset = BadPassword.objects.all()
    serializer_class = BadPasswordSerializer



class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer



class HistoryViewSet(viewsets.ModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer



class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer



class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer



class QuizSessionViewSet(viewsets.ModelViewSet):
    queryset = QuizSession.objects.all()
    serializer_class = QuizSessionSerializer



class UserAnswerViewSet(viewsets.ModelViewSet):
    queryset = UserAnswer.objects.all()
    serializer_class = UserAnswerSerializer



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
