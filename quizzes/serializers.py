from rest_framework import serializers
from .models import Quiz, Question, Option, UserAnswer, QuizAttempt


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'questions', 'questions_count']

    def get_questions_count(self, obj):
        return obj.get_questions_count()


class QuizListSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'questions_count']

    def get_questions_count(self, obj):
        return obj.get_questions_count()


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['question', 'selected_option']


class AnswerSubmissionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        )
    )

    def validate_answers(self, answers):
        for answer in answers:
            if 'question_id' not in answer or 'option_id' not in answer:
                raise serializers.ValidationError("Каждый ответ должен содержать question_id и option_id")
        return answers


class ResultOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']


class ResultQuestionSerializer(serializers.ModelSerializer):
    options = ResultOptionSerializer(many=True, read_only=True)
    selected_option = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'selected_option', 'is_correct']

    def get_selected_option(self, obj):
        user = self.context.get('user')
        try:
            user_answer = UserAnswer.objects.get(user=user, question=obj)
            return user_answer.selected_option_id
        except UserAnswer.DoesNotExist:
            return None

    def get_is_correct(self, obj):
        user = self.context.get('user')
        try:
            user_answer = UserAnswer.objects.get(user=user, question=obj)
            return user_answer.selected_option.is_correct
        except UserAnswer.DoesNotExist:
            return False


class QuizResultSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'questions', 'score']

    def get_questions(self, obj):
        user = self.context.get('user')
        questions = obj.questions.all()
        return ResultQuestionSerializer(questions, many=True, context={'user': user}).data

    def get_score(self, obj):
        user = self.context.get('user')
        return obj.get_score(user)


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz_id', 'quiz_title', 'score', 'completed_at']
        read_only_fields = ['completed_at']