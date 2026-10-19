from django.conf import settings
from django.db import models


class Newsletter(models.Model):

  class Status(models.TextChoices):
    DRAFT = "draft", "Чернетка"
    SCHEDULED = "scheduled", "Запланована"
    SENDING = "sending", "Відправляється"
    SENT = "sent", "Відправлена"
    FAILED = "failed", "Помилка відправки"

  class Channel(models.TextChoices):
    EMAIL = "email", "Тільки Email"
    TELEGRAM = "telegram", "Тільки Telegram"
    BOTH = "both", "Email та Telegram"

  title = models.CharField("Тема / Заголовок", max_length=255)
  body = models.TextField("Текст повідомлення")

  image = models.ImageField(
      "Зображення / Банер",
      upload_to="newsletters/images/",
      blank=True,
      null=True,
  )

  channel = models.CharField(
      "Канал відправки",
      max_length=20,
      choices=Channel.choices,
      default=Channel.BOTH,
  )
  status = models.CharField(
      "Статус",
      max_length=20,
      choices=Status.choices,
      default=Status.DRAFT,
  )

  scheduled_at = models.DateTimeField(
      "Заплановано на",
      blank=True,
      null=True,
      help_text="Залиште порожнім для негайної відправки",
  )
  sent_at = models.DateTimeField("Фактично відправлено", blank=True, null=True)

  total_recipients = models.PositiveIntegerField("Усього отримувачів", default=0)
  success_count = models.PositiveIntegerField("Успішно відправлено", default=0)
  fail_count = models.PositiveIntegerField("Помилок доставки", default=0)

  author = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.SET_NULL,
      null=True,
      verbose_name="Автор",
      limit_choices_to={"is_staff": True},
  )
  created_at = models.DateTimeField("Дата створення", auto_now_add=True)
  updated_at = models.DateTimeField("Дата оновлення", auto_now=True)

  class Meta:
    verbose_name = "Розсилка"
    verbose_name_plural = "Розсилки"
    ordering = ["-created_at"]

  def __str__(self):
    return f"[{self.get_channel_display()}] {self.title} ({self.get_status_display()})"