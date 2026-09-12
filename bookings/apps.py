from django.apps import AppConfig


class BookingsConfig(AppConfig):
    name = 'bookings'
    verbose_name = 'Бронювання'

    def ready(self):
        import bookings.signals