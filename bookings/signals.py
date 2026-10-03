import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config import ADMIN_CHAT_ID, BOT_TOKEN
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Booking


async def _send_telegram_notification(text: str, reply_markup=None):
    async with Bot(token=BOT_TOKEN) as async_bot:
        await async_bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


@receiver(post_save, sender=Booking)
def notify_admin_on_new_booking(sender, instance, created, **kwargs):
    if created:
        comment_text = (
            f"<b>Коментар:</b> {instance.comment}\n"
            if instance.comment
            else ""
        )

        text = (
            f"🔔 <b>Нове бронювання #{instance.id}!</b>\n\n"
            f"<b>Тур:</b> {instance.tour_date.tour.title}\n"
            f"<b>Дати:</b> {instance.tour_date.start_date.strftime('%d.%m.%Y')} — {instance.tour_date.end_date.strftime('%d.%m.%Y')}\n"
            f"<b>Клієнт:</b> {instance.customer_name}\n"
            f"<b>Телефон:</b> {instance.customer_phone}\n"
            f"<b>Email:</b> {instance.customer_email}\n"
            f"<b>Осіб:</b> {instance.persons_count}\n"
            f"<b>Сума:</b> €{instance.total_price}\n"
            f"{comment_text}"
            f"<b>Залишилось місць:</b> {instance.tour_date.available_seats}\n"
            f"<b>Статус:</b> {instance.get_status_display()}"
        )

        keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ Підтвердити",
                                callback_data=f"confirm_booking:{instance.id}",
                            ),
                            InlineKeyboardButton(
                                text="❌ Скасувати",
                                callback_data=f"cancel_booking:{instance.id}",
                            ),
                        ]
                    ]
                )

        try:
            asyncio.run(_send_telegram_notification(text, reply_markup=keyboard))
        except Exception as e:
            print(f"Помилка відправки сповіщення в Telegram: {e}")