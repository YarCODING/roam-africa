from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from ..keyboards import get_main_keyboard
from ..services import link_telegram_account

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    args = command.args

    if args and "-" in args:
        try:
            uidb36, token = args.split("-", 1)
            user = await link_telegram_account(uidb36, token, message.from_user.id)

            if user:
                await message.answer(
                    f"🎉 <b>Успішно!</b>\n\n"
                    f"Акаунт <b>{user.username} ({user.email})</b> успішно прив'язано до Telegram!",
                    parse_mode="HTML"
                )
                return
            else:
                await message.answer("❌ Недійсне або застаріле посилання авторизації.")
                return
        except Exception as e:
            print(f"Помилка розбору токена: {e}")

    first_name = message.from_user.first_name if message.from_user else "мандрівнику"

    welcome_text = (
        f"Вітаємо, {first_name}! 👋\n\n"
        f"Раді бачити вас у боті <b>Roam Africa</b>. Ми створюємо експедиції "
        f"та авторські подорожі найвищого рівня для тих, хто цінує глибокий досвід "
        f"і надійну організацію.\n\n"
        f"Оберіть, що вас цікавить:"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )