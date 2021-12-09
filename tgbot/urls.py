from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from dtb.settings import TELEGRAM_TOKEN
from . import views

urlpatterns = [  
    path(f'tgapi/{TELEGRAM_TOKEN}/', csrf_exempt(views.TelegramBotWebhookView.as_view())),
]
