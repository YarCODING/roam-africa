from django.urls import path
from .views import*

urlpatterns = [
    path('checkout/<int:tour_id>/', checkout_view, name='checkout'),
    path('success/<int:booking_id>/', booking_success, name='success'),
    path('list/', bookings_list, name="bookings_list"),
    path('cancel/<int:booking_id>/', cancel_booking, name="cancel_booking"),
    path('<int:booking_id>/', booking_detail, name='booking_detail'),
]