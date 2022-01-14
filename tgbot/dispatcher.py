"""
    Telegram event handlers
"""
import logging
import re
import sys
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
)

from dtb.celery import app  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN, DEBUG, TELEGRAM_LOGS_CHAT_ID
from tgbot.handlers.admin import handlers as admin_handlers
from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST
from tgbot.handlers.broadcast_message.static_text import broadcast_command
from tgbot.handlers.proxy_add_delete.handlers import proxy_service, add_proxy_1, add_proxy_2, delete_private_proxies
from tgbot.handlers.sub_only import handlers as sub_handlers
from tgbot.handlers.general.static_text import cancel_button_action, admin_command_button_text, \
    buy_subscription_button_text, token_checker_button_text, proxy_service_button_text
from tgbot.handlers.general import handlers as general_handlers
from tgbot.handlers.proxy_add_delete import handlers as proxy_add_delete_handlers
from tgbot.handlers.general.static_text import contact_button_text
from tgbot.handlers.utils import error
from tgbot.handlers.utils.static_text import (
    year_admin_subdate, forever_admin_subdate,
    one_month_admin_subdate, three_month_admin_subdate, find_user_by_username_button_text,
    broadcast_message_button_text, go_back_button_text, settings_admin_proxy_button_text,
    upload_proxy_admin_button_text, export_public_proxy_button_text, upload_user_proxy_button_text,
    delete_all_private_proxies
)
from utils.default_conversation_handler import get_conv_handler


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """

    standard_fallbacks = [MessageHandler(Filters.regex(f'^{cancel_button_action}$'), general_handlers.cancel),
                          CommandHandler('cancel', general_handlers.cancel)]

    # general
    dp.add_handler(CommandHandler("start", general_handlers.start))
    dp.add_handler(CommandHandler("help", general_handlers.help_command))
    dp.add_handler(CommandHandler("contact", general_handlers.contact))
    dp.add_handler(MessageHandler(Filters.regex(f'^{contact_button_text}$'), general_handlers.contact))
    dp.add_handler(
        MessageHandler(Filters.regex(f'^{buy_subscription_button_text}$'), general_handlers.buy_subscription))
    dp.add_handler(MessageHandler(Filters.regex(f'^{go_back_button_text}$'), general_handlers.go_back))

    # sub only commands
    token_checker_conv = get_conv_handler(
        token_checker_button_text, sub_handlers.token_checker, 'get_document',
        Filters.document.txt | Filters.regex(r'^([MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}(\n)?){1,}$'),
        sub_handlers.token_checker_2
    )
    dp.add_handler(token_checker_conv)

    # proxies
    dp.add_handler(MessageHandler(Filters.text(proxy_service_button_text), proxy_service))
    dp.add_handler(MessageHandler(Filters.text(delete_all_private_proxies), delete_private_proxies))
    add_user_proxy_conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.text(upload_user_proxy_button_text), add_proxy_1)],
        states={
            'process_new_user_proxies': [
                MessageHandler(
                    Filters.document.txt,
                    add_proxy_2
                )
            ]
        },
        fallbacks=standard_fallbacks
    )
    dp.add_handler(add_user_proxy_conv)

    # admin proxy
    dp.add_handler(MessageHandler(Filters.text(settings_admin_proxy_button_text),
                                  proxy_add_delete_handlers.add_proxy_as_admin))
    dp.add_handler(MessageHandler(Filters.text(export_public_proxy_button_text),
                                  proxy_add_delete_handlers.export_admin_proxy))
    admin_add_proxy_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.text(upload_proxy_admin_button_text), proxy_add_delete_handlers.wait_new_admin_proxy)
        ],
        states={
            'wait_txt_file': [
                MessageHandler(
                    Filters.text(['http', 'socks5', 'socks4']),
                    proxy_add_delete_handlers.wait_txt_admin_proxy
                )
            ],
            'process_new_admin_proxy': [
                MessageHandler(
                    Filters.document.txt,
                    proxy_add_delete_handlers.process_new_admin_proxy
                )
            ]
        },
        fallbacks=standard_fallbacks
    )
    dp.add_handler(admin_add_proxy_handler)

    # admin/mod commands
    dp.add_handler(CommandHandler("admin", admin_handlers.admin))
    dp.add_handler(MessageHandler(Filters.regex(f'^{admin_command_button_text}$'), admin_handlers.admin))
    dp.add_handler(CommandHandler("admin_commands", admin_handlers.admin_command_list))
    dp.add_handler(CommandHandler("add_mod", admin_handlers.add_moderator))
    dp.add_handler(CommandHandler("remove_mod", admin_handlers.remove_moderator))
    dp.add_handler(CommandHandler("stats", admin_handlers.stats))
    dp.add_handler(CommandHandler('export_users', admin_handlers.export_users))
    find_user_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(f'^{find_user_by_username_button_text}$'), admin_handlers.find_user)],
        states={
            # TODO: add proper regex
            'find_user_get_username': [
                MessageHandler(
                    Filters.all,
                    admin_handlers.continue_finding_user
                )
            ]
        },
        fallbacks=standard_fallbacks
    )
    dp.add_handler(find_user_conv_handler)
    give_access_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('gaccess', admin_handlers.give_access)],
        states={
            'give_access_get_time': [
                MessageHandler(
                    Filters.text([one_month_admin_subdate, three_month_admin_subdate,
                                  year_admin_subdate, forever_admin_subdate]),
                    admin_handlers.continue_giving_access
                )
            ]
        },
        fallbacks=standard_fallbacks
    )
    dp.add_handler(give_access_conv_handler)
    dp.add_handler(CommandHandler('raccess', admin_handlers.remove_access))

    # broadcast message
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{broadcast_command}(/s)?.*'),
                       broadcast_handlers.broadcast_command_with_message)
    )
    dp.add_handler(get_conv_handler(
        broadcast_message_button_text,
        broadcast_handlers.broadcast_command_without_message,
        'get_broadcast_message',
        Filters.regex(re.compile(f'^(?!{cancel_button_action}$).*')),
        broadcast_handlers.broadcast_command_without_message_2
    ))
    dp.add_handler(
        CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    )
    dp.add_handler(
        CallbackQueryHandler(sub_handlers.cancel_token_check, pattern='^cancel_token_checker_')
    )
    dp.add_handler(standard_fallbacks[0])
    dp.add_handler(standard_fallbacks[1])

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
# if not DEBUG:
#     set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
