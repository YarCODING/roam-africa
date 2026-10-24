from django.db import transaction
from django.db.models import F
from newsletter.tasks import send_email_task, send_telegram_message_task
from users.models import LoyaltyTier
from .models import Booking
from .pdf_utils import generate_booking_ticket_pdf


def change_booking_status(booking: Booking, new_status: str):
  old_status = booking.status
  if old_status == new_status:
    return

  with transaction.atomic():
    booking.status = new_status
    booking.save()

    if (
        new_status == Booking.Status.COMPLETED
        and old_status != Booking.Status.COMPLETED
    ):
      _update_user_loyalty_on_completion(booking)

  send_booking_status_notification(booking, old_status, new_status)


def _update_user_loyalty_on_completion(booking: Booking):
  customer = booking.customer
  if not customer:
    return

  customer.trips_count = F('trips_count') + 1
  customer.save(update_fields=['trips_count'])
  customer.refresh_from_db()

  appropriate_tier = (
      LoyaltyTier.objects.filter(min_trips__lte=customer.trips_count)
      .order_by('-min_trips')
      .first()
  )

  if appropriate_tier and customer.loyalty_tier != appropriate_tier:
    customer.loyalty_tier = appropriate_tier
    customer.save(update_fields=['loyalty_tier'])


def send_booking_status_notification(
    booking: Booking, old_status: str, new_status: str
):
  customer = booking.customer
  if not customer:
    return

  status_mapping = {
      (Booking.Status.NEW, Booking.Status.CONFIRMED): 'confirmed',
      (Booking.Status.NEW, Booking.Status.PAID): 'paid',
      (Booking.Status.CONFIRMED, Booking.Status.PAID): 'paid',
      (Booking.Status.PAID, Booking.Status.COMPLETED): 'completed',
  }

  status_changed_to = None
  if new_status == Booking.Status.CANCELED and old_status in [
      Booking.Status.NEW,
      Booking.Status.CONFIRMED,
  ]:
    status_changed_to = 'canceled'
  else:
    status_changed_to = status_mapping.get((old_status, new_status))

  if not status_changed_to:
    return

  if customer.telegram_chat_id:
    text = _get_telegram_notification_text(booking, status_changed_to)
    if text:
      send_telegram_message_task.delay(
          chat_id=customer.telegram_chat_id, message=text
      )

  verified_email = (
      customer.emailaddress_set.filter(verified=True, primary=True)
      .values_list('email', flat=True)
      .first()
  )

  if verified_email:
    title, body = _get_email_notification_content(booking, status_changed_to)
    if title and body:
      pdf_data = None
      pdf_name = f'ticket_{booking.id}.pdf'

      if status_changed_to == 'paid':
        pdf_data = generate_booking_ticket_pdf(booking)

      send_email_task.delay(
          email=verified_email,
          title=title,
          body=body,
          attachment_data=pdf_data,
          attachment_name=pdf_name,
      )


def _get_telegram_notification_text(booking: Booking, status_type: str) -> str:
  tour_title = (
      booking.tour_date.tour.title
      if booking.tour_date and booking.tour_date.tour
      else 'Тур'
  )

  if status_type == 'confirmed':
    return (
        f'✅ <b>Ваше бронювання #{booking.id} підтверджено!</b>\n\n'
        f'🌴 <b>Тур:</b> {tour_title}\n'
        f'👥 <b>Кількість осіб:</b> {booking.persons_count}\n'
        f'💰 <b>Загальна сума:</b> {booking.total_price}\n\n'
        f'Тепер ви можете перейти до оплати на сайті.'
    )
  elif status_type == 'completed':
    return (
        f'🎉 <b>Ви завершили тур {tour_title}!</b>\n\n'
        f'📅 <b>Дата закінчення:</b>'
        f' {booking.tour_date.end_date.strftime("%d.%m.%Y")}\n'
        f'📘 <b>Бронювання:</b> #{booking.id}\n\n'
        f'Тепер ви можете залишити відгук!'
    )
  elif status_type == 'canceled':
    return (
        f'❌ <b>Ваше бронювання #{booking.id} скасовано</b>\n\n'
        f'🌴 <b>Тур:</b> {tour_title}\n'
        f'📅 <b>Дата початку:</b>'
        f' {booking.tour_date.start_date.strftime("%d.%m.%Y")}\n\n'
        f'Бронювання було скасовано, оскільки воно не було оплачено вчасно.'
    )
  return ''


def _get_email_notification_content(booking: Booking, status_type: str) -> tuple:
  tour_title = (
      booking.tour_date.tour.title
      if booking.tour_date and booking.tour_date.tour
      else 'Тур'
  )

  if status_type == 'confirmed':
    title = f'Підтвердження бронювання #{booking.id} — Roam Africa'
    body = (
        f'<p>Вітаємо!</p>'
        f'<p>Ваше бронювання <strong>#{booking.id}</strong> на тур <strong>{tour_title}</strong> успішно підтверджено.</p>'
        f'<ul>'
        f'<li>Кількість осіб: {booking.persons_count}</li>'
        f'<li>Загальна сума: {booking.total_price}</li>'
        f'</ul>'
        f'<p>Тепер ви можете перейти до особистого кабінету на сайті для здійснення оплати.</p>'
    )
    return title, body
  elif status_type == 'paid':
    title = f'Оплата успішна! Ваш квиток #{booking.id} — Roam Africa'
    body = (
        f'<p>Вітаємо! Ваша оплата за тур <strong>{tour_title}</strong> успішно отримана.</p>'
        f'<p>У вкладені цього листа ви знайдете свій офіційний <strong>PDF-квиток</strong> із QR-кодом.</p>'
        f'<ul>'
        f'<li>Бронювання: #{booking.id}</li>'
        f'<li>Кількість осіб: {booking.persons_count}</li>'
        f'<li>Сума: {booking.total_price}</li>'
        f'</ul>'
        f'<p>Зберігайте квиток та підготуйте документи для поїздки. Чекаємо на вас в Африці! 🌍</p>'
    )
    return title, body
  elif status_type == 'completed':
    title = f'Ваша подорож завершена — Roam Africa'
    body = (
        f'<p>Вітаємо з успішним завершенням туру <strong>{tour_title}</strong>!</p>'
        f'<p>Сподіваємося, ця подорож залишила неймовірні емоції. Будемо раді, якщо ви залишите відгук на нашому сайті.</p>'
    )
    return title, body

  elif status_type == 'canceled':
    title = f'Бронювання #{booking.id} скасовано — Roam Africa'
    body = (
        f'<p>На жаль, ваше бронювання <strong>#{booking.id}</strong> на тур <strong>{tour_title}</strong> було скасовано через відсутність оплати вчасно.</p>'
        f'<p>Ви завжди можете забронювати тур повторно на нашому сайті.</p>'
    )
    return title, body

  return '', ''