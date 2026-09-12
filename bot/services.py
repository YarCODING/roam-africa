from asgiref.sync import sync_to_async
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import base36_to_int
from django.contrib.auth import get_user_model
from tours.models import Tour
from bookings.models import Booking

User = get_user_model()

@sync_to_async
def get_active_tours():
    return list(Tour.objects.published().select_related('country')[:10])

@sync_to_async
def get_booking_by_id(booking_id: int):
    try:
        return Booking.objects.select_related('tour_date__tour').get(id=booking_id)
    except Booking.DoesNotExist:
        return None

@sync_to_async
def get_tour_details(tour_id: int):
    """Отримання туру разом з датами, розкладом, включеннями та галереєю."""
    try:
        return Tour.objects.prefetch_related(
            'images',
            'itinerary_days',
            'inclusions',
            'dates'
        ).select_related('country').get(id=tour_id, is_active=True)
    except Tour.DoesNotExist:
        return None

@sync_to_async
def get_user_bookings(chat_id: int):
    try:
        user = User.objects.filter(telegram_chat_id=int(chat_id)).first()
        if not user:
            return None, []
        
        bookings = list(
            Booking.objects.filter(customer=user)
            .select_related('tour_date__tour')
            .order_by('-id')
        )
        return user, bookings
    except Exception as e:
        print(f"❌ Помилка отримання бронювань: {e}")
        return None, []

@sync_to_async
def get_user(chat_id: int):
    try:
        user = User.objects.filter(telegram_chat_id=int(chat_id)).first()
        if not user:
            return None
        
        return user
    except Exception as e:
        print(f"❌ Помилка отримання користувача: {e}")
        return None
    
@sync_to_async
def link_telegram_account(uidb36: str, token: str, chat_id: int):
    """Зв'язує telegram_chat_id з користувачем Django."""
    try:
            user_id = base36_to_int(uidb36)
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                user.telegram_chat_id = chat_id
                user.save()
                return user
    except Exception as e:
        print(f"Помилка авторизації: {e}")
        return None
    return None


@sync_to_async
def unlink_telegram_account(chat_id: int) -> bool:
    """Видаляє зв'язок між Telegram чатом та акаунтом сайту."""
    try:
        user = User.objects.filter(telegram_chat_id=int(chat_id)).first()
        if user:
            user.telegram_chat_id = None
            user.save(update_fields=['telegram_chat_id'])
            return True
        return False
    except Exception as e:
        print(f"❌ Помилка відв'язки акаунта: {e}")
        return False