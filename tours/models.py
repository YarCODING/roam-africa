from django.db import models
from django.utils import timezone
from datetime import timedelta

class Country(models.Model):
    name = models.CharField("Назва країни", max_length=100)
    code = models.CharField("ISO код", max_length=2, unique=True)
    slug = models.SlugField("URL slug", unique=True)
    description = models.TextField("Опис країни", blank=True)
    cover_image = models.ImageField("Обкладинка", upload_to="countries/")

    class Meta:
        verbose_name = "Країна"
        verbose_name_plural = "Країни"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"




class TourQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True)


class Tour(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Легкий"
        MEDIUM = "medium", "Середній"
        HARD = "hard", "Складний"
        EXTREME = "extreme", "Екстремальний"

    country = models.ForeignKey(
        Country, 
        on_delete=models.CASCADE, 
        related_name="tours",
        verbose_name="Країна"
    )

    title = models.CharField("Назва туру", max_length=60)
    slug = models.SlugField("URL slug", unique=True)
    description = models.TextField("Короткий опис")
    full_content = models.TextField("Повний опис", blank=True)
    cover_image = models.ImageField(
        "Обкладинка тура", 
        upload_to="tours/covers/", 
        blank=True, 
        null=True
    )

    duration_days = models.PositiveIntegerField("Тривалість (днів)")
    price_from = models.DecimalField("Ціна від (€)", max_digits=10, decimal_places=2)
    difficulty = models.CharField(
        "Складність", 
        max_length=20, 
        choices=Difficulty.choices, 
        default=Difficulty.EASY
    )

    group_size_max = models.PositiveIntegerField("Макс. кількість осіб у групі", default=10)

    is_active = models.BooleanField("Опубліковано", default=True, db_index=True)
    created_at = models.DateTimeField("Дата створення", auto_now_add=True)
    updated_at = models.DateTimeField("Дата оновлення", auto_now=True)

    objects = TourQuerySet.as_manager()

    @property
    def is_new(self):
        return self.created_at >= timezone.now() - timedelta(days=7)

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Тури"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.country.name}"


class TourImage(models.Model):
    tour = models.ForeignKey(
        Tour, 
        on_delete=models.CASCADE, 
        related_name="images", 
        verbose_name="Тур"
    )
    image = models.ImageField("Зображення", upload_to="tours/gallery/")
    caption = models.CharField("Підпис / Alt текст", max_length=255, blank=True)
    order = models.PositiveIntegerField("Порядок сортування", default=0)

    class Meta:
        verbose_name = "Фотографії з туру"
        verbose_name_plural = "Галерея туру"
        ordering = ["order", "id"]

    def __str__(self):
        return f"Фото для {self.tour.title}"



class TourDate(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Набір відкрито"
        FEW_LEFT = "few_left", "Залишилося небагато місць"
        SOLD_OUT = "sold_out", "Місць немає"
        CANCELED = "canceled", "Скасовано"

    tour = models.ForeignKey(
        Tour, 
        on_delete=models.CASCADE, 
        related_name="dates",
        verbose_name="Тур"
    )

    start_date = models.DateField("Дата початку")
    end_date = models.DateField("Дата закінчення")
    price = models.DecimalField("Точна ціна (€)", max_digits=10, decimal_places=2)
    available_seats = models.PositiveIntegerField("Вільних місць")
    status = models.CharField(
        "Статус групи", 
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN
    )

    class Meta:
        verbose_name = "Дата заїзду"
        verbose_name_plural = "Дати заїздів"
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.tour.title} ({self.start_date.strftime('%d.%m.%Y')} — {self.end_date.strftime('%d.%m.%Y')})"



class ItineraryDay(models.Model):
    tour = models.ForeignKey(
        Tour, 
        on_delete=models.CASCADE, 
        related_name="itinerary_days",
        verbose_name="Тур"
    )

    day_number = models.PositiveIntegerField("День №")
    title = models.CharField("Заголовок дня", max_length=255)
    description = models.TextField("Опис дня")
    accommodation = models.CharField("Проживання", max_length=255, blank=True)
    meals = models.CharField("Харчування", max_length=100, blank=True)

    class Meta:
        verbose_name = "Розклад програми"
        verbose_name_plural = "Розклад за днями"
        ordering = ["day_number"]
        unique_together = [["tour", "day_number"]]

    def __str__(self):
        return f"День {self.day_number}: {self.title} ({self.tour.title})"



class TourInclusion(models.Model):
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="inclusions",
        verbose_name="Тур"
    )

    text = models.CharField("Назва послуги", max_length=255)
    is_included = models.BooleanField(
        "Входить у вартість", 
        default=True,
        help_text="Входить (галочка), не входить (порожній квадрат)"
    )

    class Meta:
        verbose_name = "Включення/Виключення"
        verbose_name_plural = "Що входить / не входить"

    def __str__(self):
        prefix = "✓" if self.is_included else "✗"
        return f"{prefix} {self.text}"