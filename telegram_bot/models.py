from django.db import models

# Create your models here.

# from account.models import User
from django.conf import settings

class TelegramUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    language_code = models.CharField(max_length=10, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.telegram_id})"

    class Meta:
        verbose_name = "Telegram пользователь"
        verbose_name_plural = "Telegram пользователи"