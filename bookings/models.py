from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from django.db import transaction
from django.db.models import F
from simple_history.models import HistoricalRecords

class PromoCode(models.Model):
    DISCOUNT_TYPES = (
        ('percent', 'Відсоток'),
        ('fixed', 'Фіксована сума'),
    )
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Промокод")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent', verbose_name="Тип знижки")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Значення знижки")
    valid_from = models.DateTimeField(verbose_name="Діє з")
    valid_to = models.DateTimeField(verbose_name="Діє до")
    usage_limit = models.PositiveIntegerField(default=100, verbose_name="Ліміт використань")
    times_used = models.PositiveIntegerField(default=0, verbose_name="Скільки разів використано")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Мінімальна сума туру")

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоди"

    def __str__(self):
        return self.code

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
    persons_count = models.PositiveIntegerField("Кількість осіб", default=1, validators=[MinValueValidator(1)])
    comment = models.TextField("Коментар до бронювання", blank=True)
    status = models.CharField("Статус заявки", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)

    original_price = MoneyField("Базова вартість (до знижок)", 
        max_digits=10, decimal_places=2, default=Money(0, 'EUR'), default_currency='EUR', help_text="Ціна за всіх осіб без урахування знижок")
    
    loyalty_discount_amount = MoneyField("Знижка за лояльністю", 
        max_digits=10, decimal_places=2, default=Money(0, 'EUR'), default_currency='EUR',)
    
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Використаний промокод"
    )
    
    promo_discount_amount = MoneyField("Знижка за промокодом", 
        max_digits=10, decimal_places=2, default=Money(0, 'EUR'), default_currency='EUR',)

    total_price = MoneyField("Загальна вартість (до сплати)", 
        max_digits=10, decimal_places=2, default=Money(0, 'EUR'), default_currency='EUR',)

    reminder_sent = models.BooleanField("Нагадування надіслано", default=False)
    
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
        with transaction.atomic():
            if self.pk:
                original = Booking.objects.select_related('tour_date').get(pk=self.pk)
                
                if self.status == self.Status.CANCELED and original.status != self.Status.CANCELED:
                    tour_date = self.tour_date
                    tour_date.available_seats = F('available_seats') + self.persons_count
                    if tour_date.status == 'sold_out':
                        tour_date.status = 'open'
                    tour_date.save()
                    tour_date.refresh_from_db()
                
                elif original.status == self.Status.CANCELED and self.status != self.Status.CANCELED:
                    tour_date = self.tour_date
                    if tour_date.available_seats < self.persons_count:
                        raise ValueError("Недостатньо вільних місць для відновлення цього бронювання.")
                    tour_date.available_seats = F('available_seats') - self.persons_count
                    if tour_date.available_seats == 0:
                        tour_date.status = 'sold_out'
                    tour_date.save()
                    tour_date.refresh_from_db()

            if self.tour_date and self.tour_date.price:
                base_sum = self.tour_date.price * self.persons_count
                if not self.original_price or self.original_price.amount == 0:
                    self.original_price = base_sum
                
                loyalty_val = self.loyalty_discount_amount.amount if self.loyalty_discount_amount else Decimal('0')
                promo_val = self.promo_discount_amount.amount if self.promo_discount_amount else Decimal('0')
                
                calculated_total = self.original_price.amount - loyalty_val - promo_val
                currency = self.original_price.currency
                
                self.total_price = Money(max(calculated_total, Decimal('0')), currency)
            super().save(*args, **kwargs)