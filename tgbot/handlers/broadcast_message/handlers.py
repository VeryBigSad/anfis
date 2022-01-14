import random

import telegram
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler

from tgbot.models import User
from tgbot.tasks import broadcast_message
from .keyboard_utils import keyboard_confirm_decline_broadcasting
from .manage_data import CONFIRM_DECLINE_BROADCAST, CONFIRM_BROADCAST
from .static_text import broadcast_command, broadcast_wrong_format, error_with_html, \
    message_is_sent, declined_message_broadcasting
from ..utils import keyboard
from ..utils.decorators import admin_only_command, handler_logging, send_typing_action


@send_typing_action
@admin_only_command
@handler_logging()
def broadcast_command_without_message(update: Update, context: CallbackContext):
    """ нажать "рассылка" в админ меню """
    update.message.reply_text("Чтобы сделать рассылку, напишите ее текст ниже.\n"
                              "Вы можете использовать <b>HTML</b> форматирование.",
                              reply_markup=keyboard.cancel_keyboard(),
                              parse_mode=ParseMode.HTML)
    return 'get_broadcast_message'


@send_typing_action
@admin_only_command
@handler_logging()
def broadcast_command_without_message_2(update: Update, context: CallbackContext):
    """ если текст подходит по форматированию, отправляет сообщение подтверждения о рассылке"""
    try:
        update.message.reply_text(
            text=update.message.text,
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=keyboard_confirm_decline_broadcasting(),
        )
    except telegram.error.BadRequest as e:
        update.message.reply_text(
            text=error_with_html.format(reason=e),
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=keyboard.cancel_keyboard()
        )
        return 'get_broadcast_message'
    return ConversationHandler.END


@send_typing_action
@admin_only_command
@handler_logging()
def broadcast_command_with_message(update: Update, context):
    """ Type /broadcast <some_text>. Then check your message in HTML format and broadcast to users. """
    u = User.get_user(update, context)

    if update.message.text == broadcast_command:
        # user typed only command without text for the message.
        update.message.reply_text(
            text=broadcast_wrong_format,
            parse_mode=telegram.ParseMode.HTML,
        )
        return

    text = f"{update.message.text.replace(f'{broadcast_command} ', '')}"
    markup = keyboard_confirm_decline_broadcasting()

    try:
        update.message.reply_text(
            text=text,
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=markup,
        )
    except telegram.error.BadRequest as e:
        update.message.reply_text(
            text=error_with_html.format(reason=e),
            parse_mode=telegram.ParseMode.HTML,
        )


@send_typing_action
@admin_only_command
@handler_logging()
def broadcast_decision_handler(update: Update, context) -> None:
    # callback_data: CONFIRM_DECLINE_BROADCAST variable from manage_data.py
    """ Entered /broadcast <some_text>.
        Shows text in HTML style with two buttons:
        Confirm and Decline
    """
    broadcast_decision = update.callback_query.data[len(CONFIRM_DECLINE_BROADCAST):]

    entities_for_celery = update.callback_query.message.to_dict().get('entities')
    entities, text = update.callback_query.message.entities, update.callback_query.message.text

    if broadcast_decision == CONFIRM_BROADCAST:
        admin_text = message_is_sent
        user_ids = list(User.objects.all().values_list('user_id', flat=True))
        random.shuffle(user_ids)

        # send in async mode via celery
        broadcast_message.delay(
            user_ids=user_ids,
            text=text,
            entities=entities_for_celery,
        )
    else:
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=declined_message_broadcasting,
        )
        admin_text = text

    context.bot.edit_message_text(
        text=admin_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        entities=None if broadcast_decision == CONFIRM_BROADCAST else entities,
    )
