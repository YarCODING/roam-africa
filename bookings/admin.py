from django.contrib import admin
from django.utils.html import format_html
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "customer_phone",
        "get_tour_title",
        "persons_count",
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
            "contacted": "#2563eb",
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