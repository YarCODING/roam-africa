from datetime import date, timedelta
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from tours.models import Country, Tour, TourDate
from .models import Booking
from .tasks import update_booking_statuses_task

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class BookingAutoStatusTestCase(TestCase):

  def setUp(self):
    self.user = User.objects.create_user(
        username='testuser',
        password='password123',
        email='test@example.com',
        telegram_chat_id=None,
    )

    EmailAddress.objects.create(
        user=self.user, email='test@example.com', verified=True, primary=True
    )

    self.country = Country.objects.create(
        name='Testland',
        code='TE',
        slug='test',
    )

    self.tour = Tour.objects.create(
        title='Тестовый Тур',
        country=self.country,
        slug='test',
        description='тест',
        duration_days=5,
        price_from=2.00,
        difficulty='easy',
    )

    self.today = timezone.now().date()

  def test_auto_cancel_unpaid_booking_within_3_days(self):
    tour_date = TourDate.objects.create(
        tour=self.tour,
        start_date=self.today + timedelta(days=2),
        end_date=self.today + timedelta(days=5),
        price=100,
        available_seats=10,
    )

    booking = Booking.objects.create(
        tour_date=tour_date,
        customer=self.user,
        customer_name='Олександр',
        customer_phone='+123456789',
        customer_email='test@example.com',
        status=Booking.Status.NEW,
    )

    update_booking_statuses_task.delay()

    booking.refresh_from_db()
    self.assertEqual(booking.status, Booking.Status.CANCELED)

  def test_do_not_cancel_paid_booking_within_3_days(self):
    tour_date = TourDate.objects.create(
        tour=self.tour,
        start_date=self.today + timedelta(days=2),
        end_date=self.today + timedelta(days=5),
        price=100,
        available_seats=10,
    )

    booking = Booking.objects.create(
        tour_date=tour_date,
        customer=self.user,
        customer_name='Олександр',
        status=Booking.Status.PAID,
    )

    update_booking_statuses_task.delay()

    booking.refresh_from_db()
    self.assertEqual(booking.status, Booking.Status.PAID)

  def test_auto_complete_past_booking(self):
    tour_date = TourDate.objects.create(
        tour=self.tour,
        start_date=self.today - timedelta(days=5),
        end_date=self.today - timedelta(days=1),
        price=100,
        available_seats=10,
    )

    booking = Booking.objects.create(
        tour_date=tour_date,
        customer=self.user,
        customer_name='Олександр',
        status=Booking.Status.PAID,
    )

    update_booking_statuses_task.delay()

    booking.refresh_from_db()
    self.assertEqual(booking.status, Booking.Status.COMPLETED)