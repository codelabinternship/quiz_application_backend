from rest_framework import serializers
from .models import QuizSession

class QuizSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSession
        fields = '__all__'

