import json
from django.db.models import Count
from django.utils import timezone
from tours.models import Tour, TourDate
from bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

def dashboard_callback(request, context):
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status="new").count()
    total_tours = Tour.objects.filter(is_active=True).count() if hasattr(Tour, "is_active") else Tour.objects.count()

    upcoming_dates = (
        TourDate.objects.filter(start_date__gte=timezone.now().date())
        .select_related("tour")
        .order_by("start_date")[:8]
    )
    
    popular_tours = Tour.objects.annotate(
        booking_count=Count("dates__bookings")
    ).order_by("-booking_count")[:5]

    chart_labels = [tour.title[:20] for tour in popular_tours]
    chart_data = [tour.booking_count for tour in popular_tours]

    context.update({
        "kpi": [
            {
                "title": "Загальна кількість бронювань",
                "metric": total_bookings,
                "footer": f"Нові/Очікуються: {pending_bookings}",
            },
            {
                "title": "Активних турів",
                "metric": total_tours,
            },
            {
                "title": "Клієнтів",
                "metric": User.objects.filter(is_staff=False).count(),
            },
        ],
        "popular_tours": popular_tours,
        "chart_data": json.dumps({
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "Бронювання",
                    "data": chart_data,
                    "backgroundColor": "#9E472A",
                    "borderRadius": 6,
                    "maxBarThickness": 32,
                }
            ],
        }),
        "upcoming_dates": upcoming_dates,
    })
    return context