from django.urls import path
from .views import*

urlpatterns = [
    path("country/<slug:slug>", country_view, name="country_detail"),
    path("tour/<slug:slug>", tour_view, name="tour_detail"),
]