from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Country,
    Tour,
    TourImage,
    TourDate,
    ItineraryDay,
    TourInclusion
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tours_count")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Кількість турів")
    def tours_count(self, obj):
        return obj.tours.count()


class ItineraryDayInline(admin.StackedInline):
    model = ItineraryDay
    extra = 1
    ordering = ("day_number",)
    fieldsets = (
        (None, {
            "fields": (("day_number", "title"), "description", ("accommodation", "meals"))
        }),
    )


class TourInclusionInline(admin.TabularInline):
    model = TourInclusion
    extra = 2
    fields = ("text", "is_included")


class TourDateInline(admin.TabularInline):
    model = TourDate
    extra = 1
    fields = ("start_date", "end_date", "price", "available_seats", "status")

class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 3
    fields = ("image", "image_preview", "caption", "order")
    readonly_fields = ("image_preview",)

    @admin.display(description="Попередній перегляд")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px; border-radius: 3px; object-fit: cover;" />',
                obj.image.url
            )
        return "Фото немає"


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = (
        "cover_preview",
        "title",
        "country",
        "duration_days",
        "price_from",
        "difficulty",
        "is_active",
        "created_at"
    )
    list_filter = ("is_active", "difficulty", "country")
    search_fields = ("title", "description", "full_content")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_active", "price_from")
    
    readonly_fields = ("created_at", "updated_at", "cover_preview_large")
    
    inlines = [TourImageInline, TourDateInline, ItineraryDayInline, TourInclusionInline]

    @admin.display(description="Обкладинка")
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 3px; object-fit: cover;" />',
                obj.cover_image.url
            )
        return "—"

    @admin.display(description="Поточна обкладинка")
    def cover_preview_large(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 3px;" />',
                obj.cover_image.url
            )
        return "Обкладинка ще не завантажена"

    fieldsets = (
        ("Основна інформація", {
            "fields": ("title", "slug", "country", "is_active", "cover_image", "cover_preview_large")
        }),
        ("Деталі та параметри", {
            "fields": (
                ("duration_days", "group_size_max", "difficulty"),
                "price_from"
            )
        }),
        ("Описи", {
            "fields": ("description", "full_content")
        }),
        ("Системна інформація", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ("tour", "start_date", "end_date", "price", "available_seats", "status")
    list_filter = ("status", "start_date", "tour__country")
    search_fields = ("tour__title",)
    date_hierarchy = "start_date"