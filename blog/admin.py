from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
  list_display = ("name", "slug")
  prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "is_published",
        "created_at",
        "views_count",
    )
    list_filter = ("is_published", "category", "created_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("author", "views_count", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)