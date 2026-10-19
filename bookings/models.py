from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from simple_history.models import HistoricalRecords

class Booking(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Нове бронювання"
        CONFIRMED = "confirmed", "Підтверджено (очікує оплати)"
        PAID = "paid", "Оплачено"
        COMPLETED = "completed", "Завершено"
        CANCELED = "canceled", "Скасовано"

    tour_date = models.ForeignKey(
        'tours.TourDate', 
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

    reminder_sent = models.BooleanField(
        "Нагадування надіслано", default=False
    )
    
    created_at = models.DateTimeField("Дата створення", auto_now_add=True)

    objects = models.Manager()
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
        super().save(*args, **kwargs)