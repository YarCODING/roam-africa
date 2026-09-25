from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from tours.models import Tour

def get_main_keyboard():
    """Головне меню."""
    kb = [
        [KeyboardButton(text="🌴 Каталог турів")],
        [KeyboardButton(text="📘 Забронювати тур"), KeyboardButton(text="🧳 Мої бронювання"), KeyboardButton(text="🔍 Бронювання за номером")],
        [KeyboardButton(text="❓ Поширені запитання (FAQ)"), KeyboardButton(text="💬 Задати запитання")],
        [KeyboardButton(text="👤 Аккаунт")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_tours_inline_keyboard(tours: list[Tour]):
    buttons = [
        [InlineKeyboardButton(text=f"{tour.title} ({tour.country.name}) — від €{tour.price_from}", callback_data=f"tour_{tour.id}")]
        for tour in tours
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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