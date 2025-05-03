from django.contrib import admin
from .models import Quiz, Question, Option, UserAnswer, QuizAttempt


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ['text', 'quiz', 'order']
    list_filter = ['quiz']
    search_fields = ['text']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ['title', 'created_at', 'get_questions_count']
    search_fields = ['title', 'description']


class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'selected_option', 'is_correct', 'submitted_at']
    list_filter = ['user', 'question__quiz']
    search_fields = ['user__email', 'question__text']

    def is_correct(self, obj):
        return obj.selected_option.is_correct

    is_correct.boolean = True


class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'completed_at']
    list_filter = ['user', 'quiz']
    search_fields = ['user__email', 'quiz__title']


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)