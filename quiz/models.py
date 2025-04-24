from django.db import models

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)  # 'en', 'uz', 'ru'
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

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

class UserResult(models.Model):
    telegram_id = models.BigIntegerField()
    score = models.IntegerField(default=0)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    last_played = models.DateTimeField(auto_now=True)




