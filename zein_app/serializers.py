import re
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BadPassword
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'full_name', 'username', 'email', 'created_at', 'updated_at')



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'password')

    def validate_password(self, value):
        errors = []

        if len(value) < 8:
            errors.append("Пароль должен содержать минимум 6 символов.")
        if not re.search(r'[A-Z]', value):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r'\d', value):
            errors.append("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r'[@_!#$%^&*(),.?":{}|<>]', value):
            errors.append("Пароль должен содержать хотя бы один спецсимвол.")
        if BadPassword.objects.filter(password__iexact=value).exists():
            errors.append("Этот пароль слишком распространён. Пожалуйста, выберите другой.")

        if errors:
            raise serializers.ValidationError(errors)

        return value





    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.full_name = f"{user.first_name} {user.last_name}".strip()
        user.save()
        return user



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)



from .models import History

class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = '__all__'
        read_only_fields = ('failed', 'score', 'percent')




from .models import Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

    def validate_correct_choices(self, value):
        allowed_choices = {"A", "B", "C", "D"}
        if not all(choice in allowed_choices for choice in value):
            raise serializers.ValidationError("Each correct choice must be one of 'A', 'B', 'C', or 'D'.")
        return value





class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class BadPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadPassword
        fields = '__all__'









from .models import (
    BadPassword, Course,
    Teacher, FAQ, Contact
)




# class SubjectSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subject
#         fields = '__all__'



# class TopicSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Topic
#         fields = '__all__'



# class QuizSessionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = QuizSession
#         fields = '__all__'



# class UserAnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserAnswer
#         fields = '__all__'















from rest_framework import serializers
from .models import Subject, Topic, Question, Choice, Quiz, UserAnswer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text']


class AdminChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class QuestionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ['id', 'text', 'image']


class QuestionDetailSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'choices']


class AdminQuestionSerializer(serializers.ModelSerializer):
    choices = AdminChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'explanation', 'image', 'choices']


class TopicListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'image', 'question_count']

    def get_question_count(self, obj):
        return obj.questions.count()


class TopicDetailSerializer(serializers.ModelSerializer):
    questions = QuestionListSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'image', 'questions']


class SubjectListSerializer(serializers.ModelSerializer):
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'image', 'topic_count']

    def get_topic_count(self, obj):
        return obj.topics.count()


class SubjectDetailSerializer(serializers.ModelSerializer):
    topics = TopicListSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'image', 'topics']


class UserAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAnswer
        fields = ['id', 'question', 'selected_choice', 'is_correct']


class QuizCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = ['topic']


class QuizAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()


class QuizResultSerializer(serializers.ModelSerializer):
    topic_name = serializers.ReadOnlyField(source='topic.name')
    subject_name = serializers.ReadOnlyField(source='topic.subject.name')
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'topic_name', 'subject_name', 'score', 'total_questions',
                  'percentage', 'started_at', 'completed_at']

    def get_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        return round((obj.score / obj.total_questions) * 100, 2)


class QuizDetailSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True, read_only=True)
    topic_name = serializers.ReadOnlyField(source='topic.name')
    subject_name = serializers.ReadOnlyField(source='topic.subject.name')
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'topic_name', 'subject_name', 'status', 'score',
                  'total_questions', 'percentage', 'started_at',
                  'completed_at', 'answers']

    def get_percentage(self, obj):
        if obj.total_questions == 0:
            return 0
        return round((obj.score / obj.total_questions) * 100, 2)

















class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'



class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'



class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order']



class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


# serializers.py
from rest_framework import serializers
from .models import TelegramBot

class TelegramBotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramBot
        fields = '__all__'
