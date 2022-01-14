import html
import logging
import traceback

import telegram
from telegram import Update

from dtb.settings import TELEGRAM_LOGS_CHAT_ID
from tgbot.models import User


def send_stacktrace_to_tg_chat(update: Update, context) -> None:
    u = User.get_user(update, context)

    logging.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>{html.escape(tb_string)}'
    )

    user_message = """
😔 Что-то сломалось.
Мы постоянно добавляем новые фичи, но иногда забываем что-то поправить.
Мы уже получили все детали чтобы пофиксить это, просим прощения за неудобства!.
Вы можете вернуться к /start или написать нам в /contact
"""
    context.bot.send_message(
        chat_id=u.user_id,
        text=user_message,
    )

    admin_message = f"⚠️⚠️⚠️ for {u.tg_str}:\n{message}"[:4090] + '</pre>'
    if TELEGRAM_LOGS_CHAT_ID:
        context.bot.send_message(
            chat_id=TELEGRAM_LOGS_CHAT_ID,
            text=admin_message,
            parse_mode=telegram.ParseMode.HTML,
        )
    logging.error(admin_message)


def send_logs_to_tg_chat(user_who_had_error: User, logs: str):
    from tgbot.dispatcher import bot
    admin_message = f"⚠️⚠️⚠️ for {user_who_had_error.tg_str}:\n{logs}"[:4090]
    if TELEGRAM_LOGS_CHAT_ID:
        bot.send_message(
            chat_id=TELEGRAM_LOGS_CHAT_ID,
            text=admin_message,
            parse_mode=telegram.ParseMode.HTML,
        )
    logging.error(admin_message)
