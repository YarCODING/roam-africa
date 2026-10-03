from import_export import resources
from import_export.fields import Field
from .models import Country, Tour, TourDate


class CountryResource(resources.ModelResource):
    id = Field(attribute="id", column_name="ID")
    name = Field(attribute="name", column_name="Назва країни")
    code = Field(attribute="code", column_name="ISO код")
    slug = Field(attribute="slug", column_name="URL slug")

    class Meta:
        model = Country
        fields = ("id", "name", "code", "slug")
        export_order = ("id", "name", "code", "slug")


class TourResource(resources.ModelResource):
    id = Field(attribute="id", column_name="ID")
    title = Field(attribute="title", column_name="Назва туру")
    slug = Field(attribute="slug", column_name="URL slug")
    country_name = Field(attribute="country__name", column_name="Країна")
    price = Field(attribute="price_from", column_name="Ціна від")
    is_active = Field(attribute="is_active", column_name="Активний")

    class Meta:
        model = Tour
        fields = ("id", "title", "slug", "country_name", "price", "is_active")
        export_order = ("id", "title", "slug", "country_name", "price", "is_active")


class TourDateResource(resources.ModelResource):
    id = Field(attribute="id", column_name="ID")
    tour_title = Field(attribute="tour__title", column_name="Тур")
    start_date = Field(attribute="start_date", column_name="Дата початку")
    end_date = Field(attribute="end_date", column_name="Дата завершення")
    seats_total = Field(attribute="tour__group_size_max", column_name="Всього місць")
    seats_available = Field(attribute="available_seats", column_name="Вільних місць")
    price = Field(attribute="price", column_name="Ціна")

    class Meta:
        model = TourDate
        fields = ("id", "tour_title", "start_date", "end_date", "seats_total", "seats_available", "price")
        export_order = ("id", "tour_title", "start_date", "end_date", "seats_total", "seats_available", "price")