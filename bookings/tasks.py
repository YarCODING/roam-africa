from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Booking
from .services import change_booking_status
from newsletter.tasks import send_telegram_message_task

@shared_task(name="update_booking_statuses", bind=True, ignore_result=True)
def update_booking_statuses_task(self):
    today = timezone.now().date()
    cancel_threshold_date = today + timedelta(days=3)

    unpaid_expired_qs = Booking.objects.filter(
        tour_date__start_date__lte=cancel_threshold_date,
        status__in=[Booking.Status.NEW, Booking.Status.CONFIRMED],
    ).select_related('tour_date__tour', 'customer')

    cancelled_count = 0
    for booking in unpaid_expired_qs:
        change_booking_status(booking, Booking.Status.CANCELED)
        cancelled_count += 1

    completed_qs = Booking.objects.filter(
        tour_date__end_date__lt=today, 
        status=Booking.Status.PAID
    ).select_related('tour_date__tour', 'customer')

    completed_count = 0
    for booking in completed_qs:
        change_booking_status(booking, Booking.Status.COMPLETED)
        completed_count += 1

    return f"Statuses updated: {cancelled_count} canceled, {completed_count} completed."


@shared_task(name='send_trip_reminders')
def send_trip_reminders_task():
  tomorrow = timezone.localdate() + timedelta(days=1)

  bookings_to_remind = Booking.objects.filter(
      tour_date__start_date=tomorrow, reminder_sent=False
  )

  count = 0
  for booking in bookings_to_remind:
    user = booking.user

    message_title = (
        f'✈️ Нагадування: Ваша поїздка на "{booking.tour_title}" вже завтра!'
    )
    message_body = (
        f'Вітаємо, {user.get_full_name() or user.email}!\n\n'
        f'Нагадуємо, що ваша подорож до <b>{booking.tour_title}</b> розпочинається вже завтра ({tomorrow}).\n'
        f'Перевірте ваші квитки, документи та зберіть валізи. Бажаємо незабутньої пригоди з Roam Africa! '
    )

    if user.telegram_chat_id:
      send_telegram_message_task.delay(
          chat_id=user.telegram_chat_id, 
          message=f'<b>{message_title}</b>\n\n{message_body}'
      )

    booking.reminder_sent = True
    booking.save(update_fields=['reminder_sent'])
    count += 1

  return (
      f'Надіслано нагадувань про поїздки за завтра ({tomorrow}): {count} шт.'
  )