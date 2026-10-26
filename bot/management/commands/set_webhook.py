import asyncio
from django.core.management.base import BaseCommand
from ...config import bot

class Command(BaseCommand):
    def handle(self, *args, **options):
        webhook_url = "https://roamafrica.onrender.com/webhooks/telegram/"

        async def set_hook():
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(url=webhook_url)
            self.stdout.write(self.style.SUCCESS(f"Вебхук налаштовано за адресою: {webhook_url}"))

        asyncio.run(set_hook())