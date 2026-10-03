from import_export import resources
from import_export.fields import Field
from .models import Booking


class BookingResource(resources.ModelResource):
    id = Field(attribute="id", column_name="ID")
    customer_name = Field(attribute="customer_name", column_name="Ім'я клієнта")
    customer_phone = Field(attribute="customer_phone", column_name="Телефон")
    customer_email = Field(attribute="customer_email", column_name="Email")
    tour_title = Field(attribute="tour_date__tour__title", column_name="Тур")
    persons_count = Field(attribute="persons_count", column_name="Кількість осіб")
    status = Field(attribute="status", column_name="Статус")
    created_at = Field(attribute="created_at", column_name="Дата створення")

    class Meta:
        model = Booking
        fields = (
            "id",
            "customer_name",
            "customer_phone",
            "customer_email",
            "tour_title",
            "persons_count",
            "status",
            "created_at",
        )
        export_order = (
            "id",
            "customer_name",
            "customer_phone",
            "customer_email",
            "tour_title",
            "persons_count",
            "status",
            "created_at",
        )