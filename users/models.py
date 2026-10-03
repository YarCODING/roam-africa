from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static

class CustomUser(AbstractUser):
    image = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField("Ім'я для відображення", max_length=20, null=True, blank=True)
    info = models.TextField("Інфо", null=True, blank=True)
    stripe_customer_id = models.CharField("Stripe Customer ID", max_length=255, blank=True, null=True)
    telegram_chat_id = models.BigIntegerField("Telegram Chat ID", null=True, blank=True, unique=True)

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