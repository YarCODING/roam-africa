from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from users.admin import is_senior_staff
from django.utils.html import format_html
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.contrib.filters.admin import SliderNumericFilter, RangeDateFilter
from import_export.admin import ImportExportMixin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Country,
    Tour,
    TourImage,
    TourDate,
    ItineraryDay,
    TourInclusion,
    TourReview
)
from .resources import CountryResource, TourResource, TourDateResource


@admin.register(Country)
class CountryAdmin(ImportExportMixin, SimpleHistoryAdmin, ModelAdmin):
    resource_classes = [CountryResource]
    
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = ("name", "slug", "tours_count")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Кількість турів")
    def tours_count(self, obj):
        return obj.tours.count()


class ItineraryDayInline(StackedInline):
    model = ItineraryDay
    extra = 1
    ordering = ("day_number",)
    fieldsets = (
        (None, {
            "fields": (("day_number", "title"), "description", ("accommodation", "meals"))
        }),
    )


class TourInclusionInline(TabularInline):
    model = TourInclusion
    extra = 2
    fields = ("text", "is_included")


class TourDateInline(TabularInline):
    model = TourDate
    extra = 1
    fields = ("start_date", "end_date", "price", "available_seats", "status")

class TourImageInline(TabularInline):
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

class TourPriceSliderFilter(SliderNumericFilter):
    MAX_DECIMALS = 0
    STEP = 100


@admin.register(Tour)
class TourAdmin(ImportExportMixin, SimpleHistoryAdmin, ModelAdmin):
    resource_classes = [TourResource]
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_filter_submit = True 

    list_display = (
        "cover_preview",
        "title",
        "country",
        "duration_days",
        "price_from",
        "difficulty",
        "is_active",
        "manager",
        "created_at"
    )
    list_filter = ("is_active", "difficulty", "country")
    list_filter += (
        ("price_from", TourPriceSliderFilter),
    )
    search_fields = ("title", "description", "full_content", "manager")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_active", "price_from", "manager")
    
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_senior_staff(request.user):
            return qs
        return qs.filter(manager=request.user)

    def has_delete_permission(self, request, obj=None):
        return is_senior_staff(request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manager" and not is_senior_staff(request.user):
            kwargs["queryset"] = request.user.__class__.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.manager:
            obj.manager = request.user
        super().save_model(request, obj, form, change)


@admin.register(TourDate)
class TourDateAdmin(ImportExportMixin, SimpleHistoryAdmin, ModelAdmin):
    resource_classes = [TourDateResource]
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_filter_submit = True

    list_display = ("tour", "start_date", "end_date", "price", "available_seats", "status")
    list_filter = ("status", "start_date", "tour__country")
    list_filter += (
            ("price", TourPriceSliderFilter),
            ("start_date", RangeDateFilter),
            ("end_date", RangeDateFilter),
        )
    search_fields = ("tour__title",)
    date_hierarchy = "start_date"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_senior_staff(request.user):
            return qs
        return qs.filter(tour__manager=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tour" and not is_senior_staff(request.user):
            kwargs["queryset"] = Tour.objects.filter(manager=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return is_senior_staff(request.user)


@admin.register(TourReview)
class TourReviewAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ("user", "tour", "rating_total", "rating_guide", "rating_program", "rating_logistic")