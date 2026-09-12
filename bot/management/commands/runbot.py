import asyncio
import logging
from django.core.management.base import BaseCommand
from bot.config import bot, dp
from bot.handlers import main_router

class Command(BaseCommand):
    help = "Запуск Telegram бота"

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )

        async def main():
            dp.include_router(main_router)
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)

        asyncio.run(main())
