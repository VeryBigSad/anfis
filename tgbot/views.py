import json
import logging

from django.http import JsonResponse
from django.views import View
from tgbot.handlers.dispatcher import process_telegram_event

from dtb.settings import DEBUG

logger = logging.getLogger(__name__)


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again. 
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        if DEBUG:
            logger.debug("New event")
            process_telegram_event(json.loads(request.body))
        else:  
            # Process Telegram event in Celery worker (async)
            # Don't forget to run it and & Redis (message broker for Celery)! 
            # Read Procfile for details
            # You can run all of these services via docker-compose.yml
            process_telegram_event.delay(json.loads(request.body))
        return JsonResponse({"ok": "POST request processed"})
    
    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request received! But nothing done"})
