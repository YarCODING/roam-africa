from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


class Category(models.Model):
  name = models.CharField(max_length=100, unique=True, verbose_name="Категорія")
  slug = models.SlugField(max_length=100, unique=True)

  class Meta:
    verbose_name = "Категорія блогу"
    verbose_name_plural = "Категорії блогу"

  def __str__(self):
    return self.name


class Article(models.Model):
  title = models.CharField(max_length=200, verbose_name="Заголовок")
  slug = models.SlugField(max_length=200, unique=True, blank=True)
  category = models.ForeignKey(
      Category,
      on_delete=models.SET_NULL,
      null=True,
      related_name="articles",
      verbose_name="Категорія",
  )
  author = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      verbose_name="Автор",
  )
  image = models.ImageField(
      upload_to="blog_images/", verbose_name="Головне зображення"
  )
  content = models.TextField(verbose_name="Вміст")
  snippet = models.TextField(
      max_length=300,
      blank=True,
      verbose_name="Короткий опис",
  )

  created_at = models.DateTimeField(
      auto_now_add=True, verbose_name="Дата створення"
  )
  updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
  is_published = models.BooleanField(
      default=True, verbose_name="Опубліковано"
  )
  views_count = models.PositiveIntegerField(
      default=0, verbose_name="Перегляди"
  )

  history = HistoricalRecords()

  class Meta:
    verbose_name = "Стаття блогу"
    verbose_name_plural = "Статті блогу"
    ordering = ["-created_at"]

  def __str__(self):
    return self.title

  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = slugify(self.title)
    super().save(*args, **kwargs)

  def get_absolute_url(self):
    return reverse("blog_detail", kwargs={"slug": self.slug})