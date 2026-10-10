import io
import zipfile
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.http import HttpResponse
from django.urls import reverse
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from import_export.admin import ImportExportModelAdmin
from users.admin import is_senior_staff
from django.utils.html import format_html
from .models import Booking
from tours.models import TourDate
from unfold.decorators import action

from .resources import BookingResource
from .pdf_utils import generate_booking_ticket_pdf

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

    actions = ['download_pdf_tickets']

    @action(description="Завантажити PDF-квитки (ZIP якщо декілька)", icon="download")
    def download_pdf_tickets(self, request, queryset):
        count = queryset.count()
        
        if count == 0:
            return None

        if count == 1:
            booking = queryset.first()
            pdf_bytes = generate_booking_ticket_pdf(booking)
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.id}.pdf"'
            return response

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for booking in queryset:
                pdf_bytes = generate_booking_ticket_pdf(booking)
                filename = f"Ticket_{booking.id}.pdf"
                zip_file.writestr(filename, pdf_bytes)

        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="Roam_Africa_Tickets.zip"'
        return response

    actions_detail = ["download_pdf_detail_action", "verify_ticket_detail_action"]

    @action(description="Завантажити PDF-квиток", icon="file_download")
    def download_pdf_detail_action(self, request, object_id: int):
        booking = self.get_object(request, object_id)
        pdf_bytes = generate_booking_ticket_pdf(booking)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.id}.pdf"'
        return response

    @action(description="Відкрити перевірку (QR)", icon="qr_code_scanner")
    def verify_ticket_detail_action(self, request, object_id: int):
        from django.shortcuts import redirect
        url = reverse('verify_booking', args=[object_id])
        return redirect(url)

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