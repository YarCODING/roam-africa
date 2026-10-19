from django.db import transaction
from .models import Booking

def change_booking_status(booking: Booking, new_status: str):
    old_status = booking.status
    if old_status == new_status:
        return

    with transaction.atomic():
        if old_status == Booking.Status.NEW and new_status == Booking.Status.CONFIRMED:
            booking.tour_date.available_seats = max(
                0, booking.tour_date.available_seats - booking.persons_count
            )
            booking.tour_date.save(update_fields=['available_seats'])

        booking.status = new_status
        booking.save()

    send_booking_status_notification(booking, old_status, new_status)


def send_booking_status_notification(booking: Booking, old_status: str, new_status: str):
    if not booking.customer or not booking.customer.telegram_chat_id:
        return

    status_mapping = {
        (Booking.Status.NEW, Booking.Status.CONFIRMED): 'confirmed',
        (Booking.Status.PAID, Booking.Status.COMPLETED): 'completed',
    }
    
    status_changed_to = None
    if new_status == Booking.Status.CANCELED and old_status in [Booking.Status.NEW, Booking.Status.CONFIRMED]:
        status_changed_to = 'canceled'
    else:
        status_changed_to = status_mapping.get((old_status, new_status))

    if not status_changed_to:
        return

    text = _get_telegram_notification_text(booking, status_changed_to)
    if text:
        from newsletter.tasks import send_telegram_message_task
        send_telegram_message_task.delay(
            chat_id=booking.customer.telegram_chat_id, 
            message=text
        )


def _get_telegram_notification_text(booking: Booking, status_type: str) -> str:
    tour_title = booking.tour_date.tour.title if booking.tour_date and booking.tour_date.tour else 'Тур'

    if status_type == 'confirmed':
        return (
            f'✅ <b>Ваше бронювання #{booking.id} підтверджено!</b>\n\n'
            f'🌴 <b>Тур:</b> {tour_title}\n'
            f'👥 <b>Кількість осіб:</b> {booking.persons_count}\n'
            f'💰 <b>Загальна сума:</b> €{booking.total_price}\n\n'
            f'Тепер ви можете перейти до оплати на сайті.'
        )
    elif status_type == 'completed':
        return (
            f'🎉 <b>Ви завершили тур {tour_title}!</b>\n\n'
            f'📅 <b>Дата закінчення:</b> {booking.tour_date.end_date.strftime("%d.%m.%Y")}\n'
            f'📘 <b>Бронювання:</b> #{booking.id}\n\n'
            f'Тепер ви можете залишити відгук!'
        )
    elif status_type == 'canceled':
        return (
            f'❌ <b>Ваше бронювання #{booking.id} скасовано</b>\n\n'
            f'🌴 <b>Тур:</b> {tour_title}\n'
            f'📅 <b>Дата початку:</b> {booking.tour_date.start_date.strftime("%d.%m.%Y")}\n\n'
            f'Бронювання було скасовано, оскільки воно не було оплачено вчасно.'
        )
    return ''