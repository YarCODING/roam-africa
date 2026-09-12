import asyncio
from django.db.models.signals import post_save
from django.dispatch import receiver
from aiogram import Bot
from django.conf import settings
from .models import Booking
from bot.config import BOT_TOKEN, ADMIN_CHAT_ID

async def _send_telegram_notification(text: str):
    """Створює окремий екземпляр бота на час відправки та закриває його сесію."""
    async with Bot(token=BOT_TOKEN) as async_bot:
        await async_bot.send_message(
            chat_id=ADMIN_CHAT_ID, 
            text=text, 
            parse_mode="HTML"
        )

@receiver(post_save, sender=Booking)
def notify_admin_on_new_booking(sender, instance, created, **kwargs):
    """Насилає сповіщення в Telegram при створенні нового бронювання."""
    if created:
        text = (
            f"🔔 <b>Нове бронювання #{instance.id}!</b>\n\n"
            f"<b>Тур:</b> {instance.tour_date.tour.title}\n"
            f"<b>Дати:</b> {instance.tour_date.start_date.strftime('%d.%m.%Y')} — {instance.tour_date.end_date.strftime('%d.%m.%Y')}\n"
            f"<b>Клієнт:</b> {instance.customer_name}\n"
            f"<b>Телефон:</b> {instance.customer_phone}\n"
            f"<b>Осіб:</b> {instance.persons_count}\n"
            f"<b>Сума:</b> €{instance.total_price}"
        )
        
        try:
            # Викликаємо локальну асинхронну функцію
            asyncio.run(_send_telegram_notification(text))
        except Exception as e:
            print(f"Помилка відправки сповіщення в Telegram: {e}")