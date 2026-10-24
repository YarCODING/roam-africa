from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static

class LoyaltyTier(models.Model):
    name = models.CharField(max_length=50, verbose_name="Назва рівня")
    min_trips = models.PositiveIntegerField(default=0, verbose_name="Мін. кількість поїздок")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Відсоток знижки")

    icon_class = models.CharField(max_length=50, default="fa-medal", verbose_name="Іконка")
    bg_color = models.CharField(max_length=30, default="#3b82f6", verbose_name="Колір фону")
    text_color = models.CharField(max_length=30, default="#ffffff", verbose_name="Колір тексту/іконки")

    class Meta:
        verbose_name = "Рівень лояльності"
        verbose_name_plural = "Рівні лояльності"

    def __str__(self):
        return f"{self.name} ({self.discount_percent}%)"



class CustomUser(AbstractUser):
    image = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField("Ім'я для відображення", max_length=20, null=True, blank=True)
    info = models.TextField("Інфо", null=True, blank=True)
    stripe_customer_id = models.CharField("Stripe Customer ID", max_length=255, blank=True, null=True)
    telegram_chat_id = models.BigIntegerField("Telegram Chat ID", null=True, blank=True, unique=True)

    trips_count = models.PositiveIntegerField(default=0, verbose_name="Кількість поїздок")
    loyalty_tier = models.ForeignKey(
        LoyaltyTier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Рівень лояльності"
    )
    
    is_subscribed_to_newsletter = models.BooleanField("Підписан на розсилку", default=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.username
    
    @property
    def name(self):
        return self.displayname if self.displayname else self.username
    
    @property
    def avatar(self):
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except Exception:
                pass
        return static('images/avatar.png')

    # unfold
    @property
    def avatar_url(self) -> str | None:
        if self.image and hasattr(self.image, 'url'):
            try:
                return self.image.url
            except Exception:
                pass
        return static('images/avatar.png')