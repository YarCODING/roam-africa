import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aiogram.types import Update
from .config import bot, dp
from .handlers import main_router

logger = logging.getLogger(__name__)

if not dp.sub_routers:
    dp.include_router(main_router)

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            update = Update.model_validate(body, context={"bot": bot})
            await dp.feed_update(bot, update)
            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.exception("Error processing Telegram webhook")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "invalid method"}, status=405)