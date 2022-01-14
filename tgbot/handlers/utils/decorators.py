import datetime
from functools import wraps

import pytz
import telegram
from django.utils import timezone
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from dtb import settings
from dtb.settings import ENABLE_DECORATOR_LOGGING
from proxy_manager.models import Proxy
from tgbot.handlers.utils import static_text, keyboard
from tgbot.models import UserActionLog, User


def send_typing_action(func):
    """ Sends typing action while processing func command. """

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=telegram.ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def command_requires_proxy(func):
    """ doesn't do anything if there aren't any proxies up rn """

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        max_requests_until_swap = 10000
        u = User.get_user(update, context)
        proxy_list = Proxy.objects.filter(
            does_work=True,
            owner=None,
            request_count_from_last_check__lt=max_requests_until_swap
        ).union(Proxy.objects.filter(
            does_work=True,
            owner=u,
            request_count_from_last_check__lt=max_requests_until_swap
        ))
        if proxy_list.exists():
            return func(update, context, *args, **kwargs)
        update.message.reply_text('Сорян, в данный момент в боте нет свободных прокси, '
                                  'поэтому ты не можешь выполнить это действие.\n'
                                  '<b>Админы уже оповещены об этом! Попробуй через несколько минут.</b>',
                                  parse_mode=ParseMode.HTML)
        context.bot.send_message(
            chat_id=settings.TELEGRAM_LOGS_CHAT_ID,
            text=f'{u.tg_str} только что проебался из-за отсутствия прокси! ДОБАВЬ!!'
        )

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
        elif settings.IGNORE_ADMIN_COMMANDS_IF_USER:
            context.bot.send_message(u.user_id, static_text.SORRY_STAFF_ONLY_COMMAND)

    return handler


def mod_only_command(func):
    """ Only allows moderator users to use some command """

    @wraps(func)
    def handler(update, context, *args, **kwargs):
        u = User.get_user(update, context)
        if u.is_moderator or u.is_admin:
            return func(update, context, *args, **kwargs)
        elif settings.IGNORE_ADMIN_COMMANDS_IF_USER:
            context.bot.send_message(u.user_id, static_text.SORRY_STAFF_ONLY_COMMAND)

    return handler


def sub_only_command(func):
    """ Only allows people who have a sub to use a command """

    @wraps(func)
    def handler(update: Update, context: CallbackContext, *args, **kwargs):
        u = User.get_user(update, context)
        if u.subscription_end <= datetime.datetime.now(tz=pytz.utc):
            if u.is_admin:
                update.message.reply_text(f'ты не подписан но ты админ, так что у тебя есть доступ к солюшену!\n'
                                          f'"/gaccess {u.tg_str} чтобы выдать себе подписку.')
                return func(update, context, *args, **kwargs)
            if u.has_subscription:
                # TODO: message admin that his sub expired
                # TODO: add a command that helps him to prolong the sub
                update.message.reply_text(f"Твоя подписка кончилась столько времени назад:"
                                          f"{datetime.datetime.now() - u.subscription_end}. :(")
                u.has_subscription = False
                u.save()

            update.message.reply_text("Это саб-онли комманда. подпишись чтоб не грустить!",
                                      reply_markup=keyboard.main_keyboard_by_user_status(u))
        else:
            return func(update, context, *args, **kwargs)

    return handler
