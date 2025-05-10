from django.core.management.base import BaseCommand
from zein_app.models import Request
from telegram_bot.services.bot_service import send_telegram_notification


class Command(BaseCommand):
    help = 'Create a test request and send Telegram notification'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, default='Test User')
        parser.add_argument('--phone', type=str, default='+71234567890')

    def handle(self, *args, **options):
        name = options['name']
        phone = options['phone']

        self.stdout.write(f"Creating test request for {name} ({phone})")

        request = Request.objects.create(
            name=name,
            phone_number=phone
        )

        self.stdout.write(self.style.SUCCESS(f"Request created with ID: {request.id}"))

        try:
            result = send_telegram_notification(request)
            self.stdout.write(self.style.SUCCESS("Telegram notification sent successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send Telegram notification: {e}"))