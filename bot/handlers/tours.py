from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InputMediaPhoto

from ..keyboards import get_tours_inline_keyboard, get_tour_detail_keyboard
from ..services import get_active_tours, get_tour_details

router = Router()

@router.message(F.text == "🌴 Каталог турів")
async def show_catalog(message: Message):
    tours = await get_active_tours()
    if not tours:
        await message.answer("Наразі немає активних турів.")
        return
    
    await message.answer(
        "Ось актуальні тури:",
        reply_markup=get_tours_inline_keyboard(tours)
    )


@router.callback_query(F.data.startswith("tour_") & ~F.data.startswith(("tour_itin_", "tour_gal_", "tour_inc_", "tour_dates_")))
async def show_tour_detail(callback: CallbackQuery):
    tour_id = int(callback.data.split("_")[1])
    tour = await get_tour_details(tour_id)

    if not tour:
        await callback.answer("Тур не знайдено або він неактивний.", show_alert=True)
        return

    text = (
        f"🌴 <b>{tour.title}</b> ({tour.country.name})\n\n"
        f"⏱ <b>Тривалість:</b> {tour.duration_days} днів\n"
        f"💪 <b>Складність:</b> {tour.get_difficulty_display()}\n"
        f"👥 <b>Макс. група:</b> до {tour.group_size_max} осіб\n"
        f"💰 <b>Ціна від:</b> €{tour.price_from}\n\n"
        f"📝 <b>Опис:</b>\n{tour.description}"
    )

    if tour.cover_image:
        photo = FSInputFile(tour.cover_image.path)
        await callback.message.answer_photo(
            photo=photo, caption=text, parse_mode="HTML",
            reply_markup=get_tour_detail_keyboard(tour.id)
        )
    else:
        await callback.message.answer(
            text=text, parse_mode="HTML",
            reply_markup=get_tour_detail_keyboard(tour.id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tour_itin_"))
async def show_tour_itinerary(callback: CallbackQuery):
    tour_id = int(callback.data.split("_")[2])
    tour = await get_tour_details(tour_id)
    days = list(tour.itinerary_days.all())

    if not days:
        await callback.answer("Розклад для цього туру ще не додано.", show_alert=True)
        return

    text = f"📅 <b>Програма туру: {tour.title}</b>\n\n"
    for day in days:
        text += f"<b>День {day.day_number}: {day.title}</b>\n{day.description}\n"
        if day.accommodation:
            text += f"🏨 <i>Проживання:</i> {day.accommodation}\n"
        if day.meals:
            text += f"🍽 <i>Харчування:</i> {day.meals}\n"
        text += "\n" + "─"*15 + "\n\n"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tour_gal_"))
async def show_tour_gallery(callback: CallbackQuery):
    tour_id = int(callback.data.split("_")[2])
    tour = await get_tour_details(tour_id)
    images = list(tour.images.all())

    if not images:
        await callback.answer("У галереї цього туру немає фотографій.", show_alert=True)
        return

    media_group = []
    for idx, img_obj in enumerate(images[:10]):
        if img_obj.image:
            caption = f"📸 {tour.title}" if idx == 0 else ""
            if img_obj.caption and idx == 0:
                caption += f"\n{img_obj.caption}"
            media_group.append(InputMediaPhoto(media=FSInputFile(img_obj.image.path), caption=caption))

    if media_group:
        await callback.message.answer_media_group(media=media_group)
    else:
        await callback.answer("Помилка завантаження фотографій.", show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith("tour_inc_"))
async def show_tour_inclusions(callback: CallbackQuery):
    tour_id = int(callback.data.split("_")[2])
    tour = await get_tour_details(tour_id)
    inclusions = list(tour.inclusions.all())

    if not inclusions:
        await callback.answer("Інформація про включення відсутня.", show_alert=True)
        return

    included = [inc.text for inc in inclusions if inc.is_included]
    excluded = [inc.text for inc in inclusions if not inc.is_included]

    text = f"📋 <b>У вартість туру «{tour.title}»:</b>\n\n"
    if included:
        text += "<b>Включено:</b>\n" + "\n".join([f"✅ {item}" for item in included]) + "\n\n"
    if excluded:
        text += "<b>НЕ включено:</b>\n" + "\n".join([f"❌ {item}" for item in excluded])

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tour_dates_"))
async def show_tour_dates(callback: CallbackQuery):
    tour_id = int(callback.data.split("_")[2])
    tour = await get_tour_details(tour_id)

    if not tour:
        await callback.answer("Тур не знайдено.", show_alert=True)
        return

    dates = list(tour.dates.all())
    if not dates:
        await callback.answer("Наразі немає запланованих дат для цього туру.", show_alert=True)
        return

    text = f"🗓 <b>Актуальні дати та ціни: {tour.title}</b>\n\n"
    status_map = dict(tour.dates.model.Status.choices)

    for tour_date in dates:
        start_str = tour_date.start_date.strftime("%d.%m.%Y")
        end_str = tour_date.end_date.strftime("%d.%m.%Y")
        status_label = status_map.get(tour_date.status, tour_date.status)
        status_icon = "✅"
        if tour_date.status == "few_left":
            status_icon = "⚠️"
        elif tour_date.status in ["sold_out", "canceled"]:
            status_icon = "❌"

        text += (
            f"📅 <b>{start_str} — {end_str}</b>\n"
            f"💰 <b>Ціна:</b> €{tour_date.price}\n"
            f"👥 <b>Вільних місць:</b> {tour_date.available_seats}\n"
            f"{status_icon} <b>Статус:</b> {status_label}\n"
            f"───────────────\n"
        )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "catalog_back")
async def back_to_catalog(callback: CallbackQuery):
    tours = await get_active_tours()
    await callback.message.answer(
        "Ось актуальні тури:",
        reply_markup=get_tours_inline_keyboard(tours)
    )
    await callback.answer()