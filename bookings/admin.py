from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from import_export.admin import ImportExportModelAdmin
from users.admin import is_senior_staff
from django.utils.html import format_html
from .models import Booking
from tours.models import TourDate

from .resources import BookingResource

@admin.register(Booking)
class BookingAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_classes = [BookingResource]
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = (
        "id",
        "customer_name",
        "customer_phone",
        "get_tour_title",
        "persons_count",
        "total_price",
        "status",
        "colored_status",
        "created_at"
    )
    list_filter = ("status", "created_at", "tour_date__tour")
    search_fields = ("customer_name", "customer_phone", "customer_email")
    readonly_fields = ("created_at",)
    list_editable = ("status",)
    date_hierarchy = "created_at"

    @admin.display(description="Тур")
    def get_tour_title(self, obj):
        return obj.tour_date.tour.title

    @admin.display(description="Статус")
    def colored_status(self, obj):
        colors = {
            "new": "#d97706",
            "completed": "#505050",
            "confirmed": "#16a34a",
            "paid": "#186636",
            "canceled": "#dc2626",
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_senior_staff(request.user):
            return qs
        return qs.filter(tour_date__tour__manager=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tour_date" and not is_senior_staff(request.user):
            kwargs["queryset"] = TourDate.objects.filter(tour__manager=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return is_senior_staff(request.user)