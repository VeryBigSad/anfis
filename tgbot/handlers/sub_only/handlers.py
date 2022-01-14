import asyncio
import datetime
import os
from typing import List

from django.core.cache import cache
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler

from dtb.celery import app
from tgbot.handlers.sub_only.token_check import token_checker_async_task
from tgbot.handlers.utils import keyboard, files
from tgbot.handlers.utils.decorators import handler_logging, sub_only_command, send_typing_action, \
    command_requires_proxy
from tgbot.models import User


@send_typing_action
@command_requires_proxy
@sub_only_command
@handler_logging()
def token_checker(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        "Пришлите либо .txt файл с токенами, либо сообщение с ними (каждый с новой строки)",
        reply_markup=keyboard.cancel_keyboard()
    )
    return 'get_document'


@send_typing_action
@command_requires_proxy
@sub_only_command
@handler_logging()
def cancel_token_check(update: Update, context: CallbackContext) -> None:
    """ ends a celery task responsible for this user's token check"""
    u = User.get_user(update, context)
    update.callback_query.answer()
    data = update.callback_query.data
    user_id = data.split('cancel_token_checker_')[1]
    task_id = cache.get(f'token_checker_task_id_for_{user_id}', None)
    if task_id is None:
        update.callback_query.edit_message_reply_markup(reply_markup=keyboard.remove_inline_keyboard())
        return
    app.control.revoke(task_id, terminate=True)

    update.callback_query.edit_message_text(
        f'✅ Отмена прочека!\n'
        f'Чекнул <b>{cache.get(f"checking_tokens_{u.user_id}")}/{cache.get(f"checking_tokens_{u.user_id}_total")}</b> токенов!\n\n '
        f'⏳ Последнее изменение: {datetime.datetime.now().strftime("%X")}',
        parse_mode=ParseMode.HTML
    )
    cache.delete(f'token_checker_task_id_for_{u.user_id}')
    cache.delete(f'token_checker_task_id_for_{u.user_id}_total')
    context.bot.send_message(chat_id=user_id, text='<b>Отмена прочека токенов!</b>',
                             reply_markup=keyboard.main_keyboard_by_user_status(u),
                             parse_mode=ParseMode.HTML)


@send_typing_action
@sub_only_command
@command_requires_proxy
@handler_logging()
def token_checker_2(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)
    if update.message.document:
        # consider it a .txt
        file_id = update.message.document.file_id
        new_file = context.bot.get_file(file_id)
        filename = files.get_filepath_for_file('token_checker')
        new_file.download(filename)
        token_list = open(filename, 'r').read().split('\n')
        os.remove(filename)
    else:
        # consider it a list of tokens, each on new line
        token_list = update.message.text.split('\n')

    celery_task = master_checker_celery_task(token_list, u.user_id)
    cache.set(f'token_checker_task_id_for_{u.user_id}', celery_task.id if celery_task else 12345)
    return ConversationHandler.END


# @app.task(ignore_result=True)
def master_checker_celery_task(token_list: List, author_user_tg_id: int):
    # start the async part, which is
    asyncio.run(
        token_checker_async_task(
            token_list, author_user_tg_id
        )
    )
    cache.delete(f'token_checker_task_id_for_{author_user_tg_id}')

