from functools import wraps

import telegram
from django.utils import timezone
from telegram import Update
from telegram.ext import CallbackContext

from dtb.settings import ENABLE_DECORATOR_LOGGING
from tgbot.handlers.utils import static_text
from tgbot.models import UserActionLog, User


def send_typing_action(func):
    """ Sends typing action while processing func command. """

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=telegram.ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def handler_logging(action_name=None):
    """ Turn on this decorator via ENABLE_DECORATOR_LOGGING variable in dtb.settings """

    def decor(func):
        @wraps(func)
        def handler(update, context, *args, **kwargs):
            # doing the function first because we don't want to create/change the user model
            # before we pass it down to the actual function.
            res = func(update, context, *args, **kwargs)
            user = User.get_user(update, context)
            action = f"{func.__module__}.{func.__name__}" if not action_name else action_name
            UserActionLog.objects.create(user_id=user.user_id, action=action, created_at=timezone.now())
            return res

        return handler if ENABLE_DECORATOR_LOGGING else func

    return decor


def admin_only_command(func):
    """ Only allows admin users to use some command """

    @wraps(func)
    def handler(update: Update, context: CallbackContext, *args, **kwargs):
        u = User.get_user(update, context)
        if u.is_admin:
            return func(update, context, *args, **kwargs)
        elif u.is_moderator:
            context.bot.send_message(u.user_id, static_text.SORRY_YOU_NOT_ADMIN_MOD_ONLY)
        else:
            context.bot.send_message(u.user_id, static_text.SORRY_STAFF_ONLY_COMMAND)

    return handler


def mod_only_command(func):
    """ Only allows moderator users to use some command """

    @wraps(func)
    def handler(update, context, *args, **kwargs):
        u = User.get_user(update, context)
        if u.is_moderator or u.is_admin:
            return func(update, context, *args, **kwargs)
        else:
            context.bot.send_message(u.user_id, static_text.SORRY_STAFF_ONLY_COMMAND)

    return handler
