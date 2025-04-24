from django.db import models

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)  # 'en', 'uz', 'ru'
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    full_name = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(verbose_name="Tajriba (yil)")
    language = models.CharField(max_length=50, verbose_name="Fan yoki Til")
    photo = models.ImageField(upload_to='teachers_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.language})"

class MediaFile(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]

    file = models.FileField(upload_to='media_files/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} - {self.file.name}"


class User(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    language = models.CharField(max_length=10, choices=[('uz', 'Uzbek'), ('ru', 'Russian'), ('en', 'English')])
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name if self.last_name else ''}"


class Subject(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.FloatField(help_text="Foiz ko‘rinishida (%)")
    points = models.PositiveIntegerField(help_text="Ball ko‘rinishida (masalan 8/10)")
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField()
    taken_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.subject.name} - {self.score}%"

class Question(models.Model):
    text = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:30]}..."

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizAnswer(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='quiz_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.question.text[:30]} - {'✅' if self.is_correct else '❌'}"



class QuizSession(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='quiz_sessions')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='quiz_sessions')

    total_question = models.IntegerField()
    correct_answers = models.IntegerField()

    score_points = models.IntegerField()
    score_percent = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.subject.name} - {self.score_percent}%"


class UserResult(models.Model):
    telegram_id = models.BigIntegerField()
    score = models.IntegerField(default=0)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    last_played = models.DateTimeField(auto_now=True)


class QuizHistory(models.Model):
    user = models.ForeignKey(User, related_name='quiz_histories', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name='quiz_histories', on_delete=models.CASCADE)
    score = models.PositiveIntegerField()  # Ball
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Foiz
    date_taken = models.DateTimeField(auto_now_add=True)  # Test o'tkazilgan sana

    def __str__(self):
        return f"{self.user} - {self.subject.name} - {self.score} points"







