from django.urls import path
from .views import*

urlpatterns = [
    path("country/<slug:slug>", country_view, name="country_detail"),
    path("tour/<slug:slug>", tour_view, name="tour_detail"),
    path('tours/<slug:slug>/leave-review/', leave_review_view, name='leave_review'),
    path('tours/', tour_list, name='tour_list'),
    path('reviews/', reviews_page, name="review_list")
]