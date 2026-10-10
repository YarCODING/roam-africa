from django.db import models
from simple_history.models import HistoricalRecords
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from tours.models import TourDate
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
import requests
from bot.config import BOT_TOKEN


class BookingQuerySet(models.QuerySet):

    def update_statuses_if_needed(self):
        today = timezone.now().date()
        cancel_threshold_date = today + timedelta(days=3)

        unpaid_expired_qs = self.filter(
            tour_date__start_date__lte=cancel_threshold_date,
            status__in=[self.model.Status.NEW, self.model.Status.CONFIRMED],
        )

        if unpaid_expired_qs.exists():
            for booking in unpaid_expired_qs.select_related(
                'tour_date__tour', 'customer'
            ):
                booking.status = self.model.Status.CANCELED
                booking.save()


        completed_qs = self.filter(
            tour_date__end_date__lt=today, status=self.model.Status.PAID
        )

        if completed_qs.exists():
            for booking in completed_qs.select_related(
                'tour_date__tour', 'customer'
            ):
                booking.status = self.model.Status.COMPLETED
                booking.save()

        return self


class BookingManager(models.Manager):

    def get_queryset(self):
        return (
            BookingQuerySet(self.model, using=self._db)
            .update_statuses_if_needed()
        )


class Booking(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Нове бронювання"
        CONFIRMED = "confirmed", "Підтверджено (очікує оплати)"
        PAID = "paid", "Оплачено"
        COMPLETED = "completed", "Завершено"
        CANCELED = "canceled", "Скасовано"

    tour_date = models.ForeignKey(
        TourDate, 
        on_delete=models.PROTECT, 
        related_name="bookings",
        verbose_name="Заїзд"
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='bookings',
        verbose_name='Клієнт'
    )
    
    customer_name = models.CharField("Ім'я клієнта", max_length=100)
    customer_phone = models.CharField("Телефон", max_length=50)
    customer_email = models.EmailField("Email")
    persons_count = models.PositiveIntegerField(
        "Кількість осіб", 
        default=1,
        validators=[MinValueValidator(1)]
    )
    comment = models.TextField("Коментар до бронювання", blank=True)
    status = models.CharField(
        "Статус заявки", 
        max_length=20, 
        choices=Status.choices, 
        default=Status.NEW,
        db_index=True
    )

    total_price = MoneyField(
        "Загальна вартість", 
        max_digits=10, 
        decimal_places=2, 
        default=Money(0, 'EUR'),
        default_currency='EUR',
    )

    created_at = models.DateTimeField("Дата створення", auto_now_add=True)

    objects = BookingManager()

    base_objects = models.Manager()

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Бронювання"
        verbose_name_plural = "Бронювання"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Бронювання #{self.id} — {self.customer_name} ({self.tour_date.tour.title})"

    def save(self, *args, **kwargs):
            if self.tour_date and self.tour_date.price:
                self.total_price = self.tour_date.price * self.persons_count

            is_new = self.pk is None
            status_changed_to = None

            if not is_new:
                old_status = Booking.base_objects.filter(pk=self.pk).values_list('status', flat=True).first()

                if old_status != self.status:
                    if old_status == self.Status.NEW and self.status == self.Status.CONFIRMED:
                        status_changed_to = 'confirmed'
                        self.tour_date.available_seats = max(0, self.tour_date.available_seats - self.persons_count)

                    elif old_status == self.Status.PAID and self.status == self.Status.COMPLETED:
                        status_changed_to = 'completed'
                    elif old_status in [self.Status.NEW, self.Status.CONFIRMED] and self.status == self.Status.CANCELED:
                        status_changed_to = 'canceled'

            super().save(*args, **kwargs)

            if status_changed_to and self.customer and self.customer.telegram_chat_id:
                self.send_telegram_notification(status_changed_to)

    def send_telegram_notification(self, new_status):
        token = BOT_TOKEN
        if not token:
            return

        tour_title = (
            self.tour_date.tour.title
            if self.tour_date and self.tour_date.tour
            else 'Тур'
        )

        if new_status == 'confirmed':
            text = (
                f'✅ <b>Ваше бронювання #{self.id} підтверджено!</b>\n\n'
                f'🌴 <b>Тур:</b> {tour_title}\n'
                f'👥 <b>Кількість осіб:</b> {self.persons_count}\n'
                f'💰 <b>Загальна сума:</b> €{self.total_price}\n\n'
                f'Тепер ви можете перейти до оплати на сайті.'
            )
        elif new_status == 'completed':
            text = (
                f'🎉 <b>Ви завершили тур {tour_title}!</b>\n\n'
                f'📅 <b>Дата закінчення:</b> {self.tour_date.end_date.strftime("%d.%m.%Y")}\n'
                f'📘 <b>Бронювання:</b> #{self.id}\n\n'
                f'Тепер ви можете залишити відгук!'
            )
        elif new_status == 'canceled':
            text = (
                f'❌ <b>Ваше бронювання #{self.id} скасовано</b>\n\n'
                f'🌴 <b>Тур:</b> {tour_title}\n'
                f'📅 <b>Дата початку:</b> {self.tour_date.start_date.strftime("%d.%m.%Y")}\n\n'
                f'Бронювання було скасовано, оскільки воно не было оплачено вчасно (за 3 дні до початку тура).'
            )

        url = f'https://api.telegram.org/bot{token}/sendMessage'
        payload = {
            'chat_id': self.customer.telegram_chat_id,
            'text': text,
            'parse_mode': 'HTML',
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f'❌ Помилка надсилання сповіщення в Telegram: {e}')