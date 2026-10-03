from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from tours.models import Tour, TourDate

def get_main_keyboard():
    """Головне меню."""
    kb = [
        [KeyboardButton(text="🌴 Каталог турів")],
        [KeyboardButton(text="📘 Забронювати тур"), KeyboardButton(text="🧳 Мої бронювання"), KeyboardButton(text="🔍 Бронювання за номером")],
        [KeyboardButton(text="❓ Поширені запитання (FAQ)"), KeyboardButton(text="💬 Задати запитання")],
        [KeyboardButton(text="👤 Аккаунт")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


PAGE_SIZE = 5

def get_tours_inline_keyboard(tours: list[Tour], page: int = 1, page_size: int = PAGE_SIZE) -> InlineKeyboardMarkup:
    total_tours = len(tours)
    total_pages = (total_tours + page_size - 1) // page_size if total_tours > 0 else 1

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_offset = (page - 1) * page_size
    end_offset = start_offset + page_size
    tours_on_page = tours[start_offset:end_offset]

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{tour.title} ({tour.country.name}) — від €{tour.price_from}",
                callback_data=f"tour_{tour.id}"
            )
        ]
        for tour in tours_on_page
    ]

    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"catalog_page_{page - 1}")
        )
    pagination_buttons.append(
        InlineKeyboardButton(text=f"{page} / {total_pages}", callback_data="noop")
    )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"catalog_page_{page + 1}")
        )

    if total_pages > 1:
        inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_tour_dates_inline_keyboard(dates: list[TourDate], page: int = 1, page_size: int = PAGE_SIZE) -> InlineKeyboardMarkup:
    total_dates = len(dates)
    total_pages = (total_dates + page_size - 1) // page_size if total_dates > 0 else 1

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_offset = (page - 1) * page_size
    end_offset = start_offset + page_size
    dates_on_page = dates[start_offset:end_offset]

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{td.tour.title} ({td.start_date.strftime('%d.%m.%Y')})",
                callback_data=f"book_td_{td.id}"
            )
        ]
        for td in dates_on_page
    ]

    pagination_buttons = []

    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"booking_page_{page - 1}")
        )
    pagination_buttons.append(
        InlineKeyboardButton(text=f"{page} / {total_pages}", callback_data="noop")
    )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"booking_page_{page + 1}")
        )

    if total_pages > 1:
        inline_keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_tour_detail_keyboard(tour_id: int) -> InlineKeyboardMarkup:
    """Кнопки під карткою туру."""
    buttons = [
        [
            InlineKeyboardButton(text="📅 Розклад програми", callback_data=f"tour_itin_{tour_id}"),
            InlineKeyboardButton(text="🖼 Галерея", callback_data=f"tour_gal_{tour_id}")
        ],
        [
            InlineKeyboardButton(text="✅ Що включено", callback_data=f"tour_inc_{tour_id}"),
            InlineKeyboardButton(text="🗓 Дати та ціни", callback_data=f"tour_dates_{tour_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад до каталогу", callback_data="catalog_back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)