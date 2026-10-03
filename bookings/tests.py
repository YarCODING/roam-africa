from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Booking
from tours.models import Tour, TourDate, Country

User = get_user_model()

class BookingAutoStatusTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            email="test@example.com",
            telegram_chat_id="5490005833",
        )

        self.country = Country.objects.create(
            name="Testland",
            code="TE",
            slug="test",
        )
        
        self.tour = Tour.objects.create(
            title="Тестовый Тур",
            country=self.country,
            slug="test",
            description="тест",
            duration_days=5,
            price_from=2.00,
            difficulty="easy",
            )
        
        self.today = timezone.now().date()

    def test_auto_cancel_unpaid_booking_within_3_days(self):
        tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=self.today + timedelta(days=2),
            end_date=self.today + timedelta(days=5),
            price=100,
            available_seats=10
        )
        
        booking = Booking.objects.create(
            tour_date=tour_date,
            customer=self.user,
            customer_name="Иван",
            customer_phone="+123456789",
            customer_email="test@example.com",
            status=Booking.Status.NEW
        )

        _ = list(Booking.objects.all())

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CANCELED)

    def test_do_not_cancel_paid_booking_within_3_days(self):
        tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=self.today + timedelta(days=2),
            end_date=self.today + timedelta(days=5),
            price=100,
            available_seats=10
        )
        
        booking = Booking.objects.create(
            tour_date=tour_date,
            customer=self.user,
            customer_name="Иван",
            status=Booking.Status.PAID
        )

        _ = list(Booking.objects.all())
        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PAID)

    def test_auto_complete_past_booking(self):
        tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=self.today - timedelta(days=5),
            end_date=self.today - timedelta(days=1),
            price=100,
            available_seats=10
        )
        
        booking = Booking.objects.create(
            tour_date=tour_date,
            customer=self.user,
            customer_name="Иван",
            status=Booking.Status.PAID
        )

        _ = list(Booking.objects.all())
        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.COMPLETED)