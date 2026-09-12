from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.db import transaction

from users.models import CustomUser
from tours.models import TourDate
from bookings.models import Booking

router = Router()

class BookingFlow(StatesGroup):
    selecting_date = State()
    entering_name = State()
    entering_email = State()
    entering_phone = State()
    entering_persons = State()
    entering_comment = State()


@sync_to_async
def get_active_tour_dates():
    return list(
        TourDate.objects.filter(tour__is_active=True)
        .select_related('tour')
        .order_by('start_date')[:10]
    )


@sync_to_async
def get_user_profile_data(chat_id: int):
    user = CustomUser.objects.filter(telegram_chat_id=int(chat_id)).first()
    if not user:
        return None
    return {'name': user.name, 'email': user.email}


@sync_to_async
def create_booking_in_db(chat_id: int, data: dict):
    try:
        user = CustomUser.objects.filter(telegram_chat_id=int(chat_id)).first()
        if not user:
            return None, "❌ Ваш акаунт не прив'язаний до сайту."

        with transaction.atomic():
            tour_date = TourDate.objects.select_for_update().get(pk=data['tour_date_id'])

            if hasattr(tour_date, 'available_seats'):
                if tour_date.available_seats < data['persons_count']:
                    return None, "❌ На жаль, на цю дату залишилося менше місць, ніж ви вказали."
                
                tour_date.available_seats -= data['persons_count']
                if tour_date.available_seats == 0:
                    tour_date.status = 'sold_out'
                tour_date.save()

            booking = Booking.objects.create(
                tour_date=tour_date,
                customer=user,
                customer_name=data['customer_name'],
                customer_email=data['customer_email'],
                customer_phone=data['customer_phone'],
                persons_count=data['persons_count'],
                comment=data['comment'],
                status=Booking.Status.NEW
            )
            return booking, None

    except TourDate.DoesNotExist:
        return None, "❌ Обрану дату заїзду не знайдено."
    except Exception as e:
        return None, f"❌ Помилка бази даних: {e}"




@router.message(F.text == "📘 Забронювати тур")
async def start_booking(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    user_info = await get_user_profile_data(chat_id)
    
    if not user_info:
        await message.answer(
            "❌ Ваш акаунт Telegram не прив'язаний до сайту.\n\n"
            "Перейдіть у налаштування свого профілю на сайті та натисніть <b>«Підключити Telegram»</b>.",
            parse_mode="HTML"
        )
        return

    dates = await get_active_tour_dates()
    if not dates:
        await message.answer("😔 Наразі немає активних турів для бронювання.")
        return

    keyboard_buttons = []
    for td in dates:
        title = f"{td.tour.title} ({td.start_date})"
        keyboard_buttons.append([InlineKeyboardButton(text=title, callback_data=f"book_td_{td.id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await state.set_state(BookingFlow.selecting_date)
    await message.answer("Оберіть тур та дату заїзду з каталогу нижче:", reply_markup=keyboard)


@router.callback_query(BookingFlow.selecting_date, F.data.startswith("book_td_"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    tour_date_id = int(callback.data.split("_")[2])
    await state.update_data(tour_date_id=tour_date_id)

    chat_id = callback.message.chat.id
    user_info = await get_user_profile_data(chat_id)
    
    await state.set_state(BookingFlow.entering_name)
    await callback.message.edit_text(
        f"Введіть ім'я для бронювання\n(або натисніть кнопку нижче, щоб залишити поточне: <b>{user_info['name']}</b>):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Залишити ({user_info['name']})", callback_data="use_profile_name")]
        ])
    )
    await callback.answer()


@router.callback_query(BookingFlow.entering_name, F.data == "use_profile_name")
async def use_profile_name_cb(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_info = await get_user_profile_data(chat_id)
    await state.update_data(customer_name=user_info['name'])
    
    await state.set_state(BookingFlow.entering_email)
    await callback.message.edit_text(
        f"Введіть пошту (Email)\n(або натисніть кнопку нижче, щоб залишити поточну: <b>{user_info['email']}</b>):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Залишити ({user_info['email']})", callback_data="use_profile_email")]
        ])
    )
    await callback.answer()


@router.message(BookingFlow.entering_name, F.text)
async def process_custom_name(message: Message, state: FSMContext):
    await state.update_data(customer_name=message.text.strip())
    
    chat_id = message.chat.id
    user_info = await get_user_profile_data(chat_id)
    
    await state.set_state(BookingFlow.entering_email)
    await message.answer(
        f"Введіть пошту (Email)\n(або натисніть кнопку нижче, щоб залишити поточну: <b>{user_info['email']}</b>):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Залишити ({user_info['email']})", callback_data="use_profile_email")]
        ])
    )


@router.callback_query(BookingFlow.entering_email, F.data == "use_profile_email")
async def use_profile_email_cb(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_info = await get_user_profile_data(chat_id)
    await state.update_data(customer_email=user_info['email'])
    
    await state.set_state(BookingFlow.entering_phone)
    await callback.message.edit_text("📱 Введіть ваш номер телефону для зв'язку:")
    await callback.answer()


@router.message(BookingFlow.entering_email, F.text)
async def process_custom_email(message: Message, state: FSMContext):
    await state.update_data(customer_email=message.text.strip())
    await state.set_state(BookingFlow.entering_phone)
    await message.answer("📱 Введіть ваш номер телефону для зв'язку:")


@router.message(BookingFlow.entering_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(customer_phone=message.text.strip())
    await state.set_state(BookingFlow.entering_persons)
    await message.answer("👥 Введіть кількість осіб для бронювання (цифрою, наприклад: '2'):", parse_mode="HTML")


@router.message(BookingFlow.entering_persons, F.text)
async def process_persons(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("⚠️ Будь ласка, введіть коректне число (більше або рівне 1):")
        return

    await state.update_data(persons_count=int(message.text))
    await state.set_state(BookingFlow.entering_comment)
    
    skip_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустити", callback_data="skip_comment")]
    ])
    await message.answer("💬 Залиште коментар до бронювання або натисніть «Пропустити»:", reply_markup=skip_kb)


@router.message(BookingFlow.entering_comment, F.text)
async def process_comment_text(message: Message, state: FSMContext):
    await finalize_booking(message, state, comment=message.text.strip())


@router.callback_query(BookingFlow.entering_comment, F.data == "skip_comment")
async def process_comment_skip(callback: CallbackQuery, state: FSMContext):
    await finalize_booking(callback.message, state, comment="")
    await callback.answer()


async def finalize_booking(message: Message, state: FSMContext, comment: str):
    data = await state.get_data()
    data['comment'] = comment
    chat_id = message.chat.id

    booking, error = await create_booking_in_db(chat_id=chat_id, data=data)
    await state.clear()

    if error:
        await message.answer(error)
        return

    response = (
        f"🎉 <b>Успішно створено бронювання #{booking.id}!</b>\n\n"
        f"🌴 <b>Тур:</b> {booking.tour_date.tour.title}\n"
        f"📅 <b>Дата заїзду:</b> {booking.tour_date.start_date}\n"
        f"👤 <b>Ім'я:</b> {booking.customer_name}\n"
        f"✉️ <b>Email:</b> {booking.customer_email}\n"
        f"📱 <b>Телефон:</b> {booking.customer_phone}\n"
        f"👥 <b>Осіб:</b> {booking.persons_count}\n"
        f"💰 <b>Сума до оплати:</b> €{booking.total_price}\n"
        f"📌 <b>Статус:</b> {booking.get_status_display()}\n\n"
        f"Переглянути ваші замовлення можна у розділі <b>«🧳 Мої бронювання»</b>."
    )
    await message.answer(response, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())