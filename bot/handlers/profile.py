from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..services import get_user, get_user_bookings, get_booking_by_id, unlink_telegram_account

router = Router()

class BookingSearch(StatesGroup):
    waiting_for_id = State()


@router.message(F.text == "👤 Аккаунт")
async def get_user_info(message: Message):
    chat_id = message.from_user.id
    user = await get_user(chat_id)
    first_name = message.from_user.first_name

    if not user:
        await message.answer(
            "❌ Ваш акаунт Telegram не прив'язаний до сайту.\n\n"
            "Перейдіть у налаштування свого профілю на сайті та натисніть <b>«Підключити Telegram»</b>.",
            parse_mode="HTML"
        )
        return

    text = (
        "👤 <b>Інформація про аккаунт:</b>\n\n"
        f"Користувач сайту: {user.username} ({user.email})\n"
        f"ID чата: {chat_id}\n"
        f"Ім'я Telegram: {first_name}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚪 Вийти з акаунта", callback_data="logout_account")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "logout_account")
async def process_logout(callback: CallbackQuery):
    chat_id = callback.from_user.id
    success = await unlink_telegram_account(chat_id)

    if success:
        await callback.message.edit_text(
            "🚪 <b>Ви успішно вийшли з аккаунта!</b>\n\n"
            "Ваш Telegram більше не прив'язаний до сайту. "
            "Щоб увійти знову, перейдіть у налаштування свого профілю на сайті та натисніть «Підключити Telegram».",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Ваш акаунт і так не був прив'язаний до Telegram-бота.", show_alert=True)
    
    await callback.answer()


@router.message(F.text == "🧳 Мої бронювання")
async def show_my_bookings(message: Message):
    chat_id = message.from_user.id
    user, bookings = await get_user_bookings(chat_id)

    if not user:
        await message.answer(
            "❌ Ваш акаунт Telegram не прив'язаний до сайту.\n\n"
            "Перейдіть у налаштування свого профілю на сайті та натисніть <b>«Підключити Telegram»</b>.",
            parse_mode="HTML"
        )
        return

    if not bookings:
        await message.answer("🧳 У вас поки немає активних бронювань.")
        return

    text = "🧳 <b>Ваші бронювання:</b>\n\n"
    for booking in bookings:
        status_map = dict(booking.Status.choices) if hasattr(booking, 'Status') else {}
        status_label = status_map.get(booking.status, booking.status)

        tour_title = "Тур"
        if hasattr(booking, 'tour_date') and booking.tour_date and booking.tour_date.tour:
            tour_title = booking.tour_date.tour.title

        text += (
            f"📋 <b>Бронювання #{booking.id}</b>\n"
            f"🌴 <b>Тур:</b> {tour_title}\n"
            f"📌 <b>Статус:</b> {status_label}\n"
            f"👥 <b>Осіб:</b> {getattr(booking, 'persons_count', 1)}\n"
            f"💰 <b>Сума:</b> €{getattr(booking, 'total_price', 0)}\n"
            f"───────────────\n"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔍 Бронювання за номером")
async def start_booking_search(message: Message, state: FSMContext):
    await state.set_state(BookingSearch.waiting_for_id)
    await message.answer("Введіть номер вашого бронювання (наприклад, 12):")


@router.message(BookingSearch.waiting_for_id)
async def process_booking_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть числове значення ID:")
        return

    booking_id = int(message.text)
    booking = await get_booking_by_id(booking_id)

    if not booking:
        await message.answer(f"❌ Бронювання #{booking_id} не знайдено.")
    else:
        status_map = dict(booking.Status.choices) if hasattr(booking, 'Status') else {}
        readable_status = status_map.get(booking.status, booking.status)
        tour_title = booking.tour_date.tour.title if hasattr(booking, 'tour_date') and booking.tour_date else "Тур"
        
        response = (
            f"📋 <b>Бронювання #{booking.id}</b>\n"
            f"🌴 <b>Тур:</b> {tour_title}\n"
            f"👤 <b>Клієнт:</b> {booking.customer_name}\n"
            f"👥 <b>Кількість осіб:</b> {booking.persons_count}\n"
            f"💰 <b>Загальна сума:</b> €{booking.total_price}\n"
            f"📌 <b>Статус:</b> {readable_status}"
        )
        await message.answer(response, parse_mode="HTML")
    
    await state.clear()