from django.urls import path
from .views import telegram_webhook

urlpatterns = [
    path("webhooks/telegram/", telegram_webhook, name="telegram_webhook"),
]