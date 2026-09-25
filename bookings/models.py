from django.db import models
from django.conf import settings
from tours.models import TourDate
from django.core.validators import MinValueValidator
import requests
from bot.config import BOT_TOKEN

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

    total_price = models.DecimalField(
        "Загальна вартість", 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )

    created_at = models.DateTimeField("Дата створення", auto_now_add=True)

    class Meta:
        verbose_name = "Бронювання"
        verbose_name_plural = "Бронювання"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Бронювання #{self.id} — {self.customer_name} ({self.tour_date.tour.title})"

    def save(self, *args, **kwargs):
        if self.tour_date and self.tour_date.price:
            self.total_price = self.tour_date.price * self.persons_count

        status_changed_to = None

        if self.pk:
            old_status = Booking.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if old_status == self.Status.NEW and self.status == self.Status.CONFIRMED:
                status_changed_to = 'confirmed'

            elif old_status == self.Status.PAID and self.status == self.Status.COMPLETED:
                status_changed_to = 'completed'

        super().save(*args, **kwargs)

        if status_changed_to and self.customer and self.customer.telegram_chat_id:
            self.send_telegram_notification(status_changed_to)

    def send_telegram_notification(self, new_status):
        token = BOT_TOKEN
        if not token:
            return

        tour_title = self.tour_date.tour.title if self.tour_date and self.tour_date.tour else "Тур"

        if new_status == 'confirmed':
            text = (
                f"✅ <b>Ваше бронювання #{self.id} підтверджено!</b>\n\n"
                f"🌴 <b>Тур:</b> {tour_title}\n"
                f"👥 <b>Кількість осіб:</b> {self.persons_count}\n"
                f"💰 <b>Загальна сума:</b> €{self.total_price}\n\n"
                f"Тепер ви можете перейти до оплати на сайті."
            )
        elif new_status == 'completed':
            text = (
                f"🎉 <b>Ви завершили тур {tour_title}!</b>\n\n"
                f"📅 <b>Дата закінчення:</b> {self.tour_date.end_date}\n"
                f"📘 <b>Бронювання:</b> #{self.id}\n\n"
                f"Тепер ви можете залишити відгук!"
            )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": self.customer.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"❌ Помилка надсилання сповіщення в Telegram: {e}")