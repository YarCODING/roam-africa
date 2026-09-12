from django.db import models
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static

class CustomUser(AbstractUser):
    image = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField("Ім'я для відображення", max_length=20, null=True, blank=True)
    info = models.TextField("Інфо", null=True, blank=True)
    stripe_customer_id = models.CharField("Stripe Customer ID", max_length=255, blank=True, null=True)
    telegram_chat_id = models.BigIntegerField("Telegram Chat ID", null=True, blank=True, unique=True)

    def __str__(self):
        return self.username
    
    @property
    def name(self):
        if self.displayname:
            name = self.displayname
        else:
            name = self.username 
        return name
    
    @property
    def avatar(self):
        try:
            avatar = self.image.url
        except:
            avatar = static('images/avatar.png')
        return avatar