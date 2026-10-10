from django.urls import path
from .views import*

urlpatterns = [
    path('checkout/<slug:slug>/', checkout_view, name='checkout'),
    path('success/<int:booking_id>/', booking_success, name='success'),
    path('list/', bookings_list, name="bookings_list"),
    path('cancel/<int:booking_id>/', cancel_booking, name="cancel_booking"),
    path('<int:booking_id>/', booking_detail, name='booking_detail'),
    path('<int:booking_id>/pay/', create_stripe_checkout_session, name='pay_booking'),
    path('payment/success/<int:booking_id>/', payment_success, name='payment_success'),
    path('payment/cancel/<int:booking_id>/', payment_cancel, name='payment_cancel'),
    path('<int:booking_id>/ticket/', download_booking_ticket, name='download_ticket'),
    path('<int:booking_id>/verify/', verify_booking_view, name='verify_booking'),
]