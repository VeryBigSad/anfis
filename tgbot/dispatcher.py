"""
    Telegram event handlers
"""
import logging
import sys
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
)

from dtb.celery import app  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN, DEBUG, TELEGRAM_LOGS_CHAT_ID
from tgbot.handlers.admin import handlers as admin_handlers
from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST
from tgbot.handlers.broadcast_message.static_text import broadcast_command
from tgbot.handlers.general import handlers as general_handlers
from tgbot.handlers.utils import error


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    # general
    dp.add_handler(CommandHandler("start", general_handlers.start))
    dp.add_handler(CommandHandler("help", general_handlers.help_command))
    dp.add_handler(CommandHandler("contact", general_handlers.contact))

    # admin/mod commands
    dp.add_handler(CommandHandler("admin", admin_handlers.admin))
    dp.add_handler(CommandHandler("add_mod", admin_handlers.add_moderator))
    dp.add_handler(CommandHandler("remove_mod", admin_handlers.remove_moderator))
    dp.add_handler(CommandHandler("stats", admin_handlers.stats))
    dp.add_handler(CommandHandler('export_users', admin_handlers.export_users))

    # broadcast message
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{broadcast_command}(/s)?.*'), broadcast_handlers.broadcast_command_with_message)
    )
    dp.add_handler(
        CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    )

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    return dp


def run_polling():
    """ Run bot in pooling mode """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    setup_dispatcher(dp)

    bot_info = Bot(TELEGRAM_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Polling of '{bot_link}' started")

    # it is really useful to send '👋' emoji to developer
    # when you run local test
    if DEBUG:
        updater.bot.send_message(text='👋', chat_id=TELEGRAM_LOGS_CHAT_ID)

    updater.start_polling()
    updater.idle()


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Start django bot 🚀',
            'stats': 'Statistics of bot 📊',
            'admin': 'Show admin info ℹ️',
            'ask_location': 'Send location 📍',
            'broadcast': 'Broadcast message 📨',
            'export_users': 'Export users.csv 👥',
        },
        'es': {
            'start': 'Iniciar el bot de django 🚀',
            'stats': 'Estadísticas de bot 📊',
            'admin': 'Mostrar información de administrador ℹ️',
            'ask_location': 'Enviar ubicación 📍',
            'broadcast': 'Mensaje de difusión 📨',
            'export_users': 'Exportar users.csv 👥',
        },
        'fr': {
            'start': 'Démarrer le bot Django 🚀',
            'stats': 'Statistiques du bot 📊',
            'admin': "Afficher les informations d'administrateur ℹ️",
            'ask_location': 'Envoyer emplacement 📍',
            'broadcast': 'Message de diffusion 📨',
            "export_users": 'Exporter users.csv 👥',
        },
        'ru': {
            'start': 'Запустить django бота 🚀',
            'stats': 'Статистика бота 📊',
            'admin': 'Показать информацию для админов ℹ️',
            'broadcast': 'Отправить сообщение 📨',
            'ask_location': 'Отправить локацию 📍',
            'export_users': 'Экспорт users.csv 👥',
        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in langs_with_commands[language_code].items()
            ]
        )


# WARNING: it's better to comment the line below in DEBUG mode.
# Likely, you'll get a flood limit control error, when restarting bot too often
if not DEBUG:
    set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
