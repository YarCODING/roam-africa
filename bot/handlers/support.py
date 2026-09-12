import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..config import bot, ADMIN_CHAT_ID

router = Router()

class SupportState(StatesGroup):
    waiting_for_question = State()


@router.message(F.text == "❓ Поширені запитання (FAQ)")
async def show_faq(message: Message):
    text = (
        "<b>Часті запитання:</b>\n\n"
        "❓ <b>Які документи потрібні?</b>\n"
        "— Закордонний паспорт (дійсний мінімум 6 місяців після поїздки).\n\n"
        "❓ <b>Як відбувається оплата?</b>\n"
        "— Оплата здійснюється за реквізитами або платіжною системою (GPay, Apple Pay...) на сайті після підтвердження заявки адміністратором.\n\n"
        "❓ <b>Чи включено страхування?</b>\n"
        "— Так, базове медичне страхування включено у вартість усіх турів."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💬 Задати запитання")
async def ask_support_start(message: Message, state: FSMContext):
    await state.set_state(SupportState.waiting_for_question)
    await message.answer(
        "Напишіть ваше запитання у повідомленні нижче. "
        "Наш менеджер відповість вам найближчим часом! 👨‍💻"
    )


@router.message(SupportState.waiting_for_question)
async def process_user_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "немає"
    question_text = message.text

    admin_message_text = (
        f"❓ <b>Нове запитання від користувача!</b>\n\n"
        f"<b>Від:</b> {user_name} ({username})\n"
        f"<b>ID користувача:</b> <code>{user_id}</code>\n\n"
        f"<b>Запитання:</b>\n{question_text}\n\n"
        f"<i>💡 Щоб відповісти, використайте функцію «Відповісти» (Reply) на це повідомлення.</i>"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message_text, parse_mode="HTML")
        await message.answer("✅ Дякуємо! Ваше запитання передано менеджеру. Очікуйте на відповідь.")
    except Exception as e:
        print(f"Помилка надсилання запитання адмінам: {e}")
        await message.answer("Виникла помилка при відправці запитання. Спробуйте пізніше.")

    await state.clear()


@router.message(
    F.chat.id == int(ADMIN_CHAT_ID),
    F.reply_to_message,
    ~F.text.startswith("/")
)
async def admin_reply_via_reply(message: Message):
    original_message = message.reply_to_message

    if not original_message.from_user.is_bot or "ID користувача:" not in (original_message.text or original_message.caption or ""):
        return

    source_text = original_message.text or original_message.caption
    match = re.search(r"ID користувача:\s*(\d+)", source_text)

    if not match:
        await message.reply("❌ Не вдалося знайти ID користувача в оригінальному повідомленні.")
        return

    target_user_id = int(match.group(1))
    reply_text = message.text
    user_notification = f"📩 <b>Відповідь від підтримки:</b>\n\n{reply_text}"

    try:
        await bot.send_message(chat_id=target_user_id, text=user_notification, parse_mode="HTML")
        await message.reply("✅ Відповідь успішно надіслано користувачеві!")
    except Exception as e:
        await message.reply(f"❌ Не вдалося надіслати повідомлення користувачеві. Можливо, він заблокував бота.\n\nПомилка: {e}")