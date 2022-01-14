from datetime import datetime, timedelta

import pytz
from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from tgbot.handlers.admin import static_text
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
from tgbot.handlers.utils.decorators import mod_only_command, admin_only_command, handler_logging, send_typing_action
from tgbot.handlers.utils.keyboard import settings_keyboard
from tgbot.models import User, UserActionLog
from tgbot.handlers.utils import keyboard
from tgbot.handlers.utils.static_text import (
    year_admin_subdate, forever_admin_subdate,
    one_month_admin_subdate, three_month_admin_subdate
)


@send_typing_action
@admin_only_command
@handler_logging()
def admin(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        static_text.admin_command_text(),
        reply_markup=keyboard.settings_keyboard()
    )


@send_typing_action
@mod_only_command
@handler_logging()
def admin_command_list(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    update.message.reply_text(static_text.secret_admin_commands)


@send_typing_action
@mod_only_command
@handler_logging()
def stats(update: Update, context: CallbackContext) -> None:
    """ Shows bot's stats """
    text = static_text.users_amount_stat.format(
        user_count=User.objects.count(),  # count may be ineffective if there are a lot of users.
        active_24=User.objects.filter(updated_at__gte=now() - timedelta(hours=24)).count()
    )

    update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@send_typing_action
@admin_only_command
@handler_logging()
def export_users(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)

    # in values argument you can specify which fields should be returned in output csv
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    update.message.reply_document(document=csv_users)


@send_typing_action
@admin_only_command
@handler_logging()
def add_moderator(update: Update, context: CallbackContext) -> None:
    text = update.message.text.replace('/add_mod ', '')
    if text == '':
        update.message.reply_text(static_text.CANT_FIND_USER_WITH_NAME_OR_ID.format(
            username_or_id=text
        ))
    u = User.get_user_by_username_or_user_id(text)
    if u is None:
        update.message.reply_text(static_text.CANT_FIND_USER_WITH_NAME_OR_ID.format(
            username_or_id=text
        ))
        return
    u.is_moderator = True
    u.save()
    mod_name = f'@{u.username if u.username else u.user_id} ({u.first_name}{f" {u.last_name}" if u.last_name else ""})'
    update.message.reply_text(static_text.MODERATOR_ADDED.format(
        mod_name=mod_name
    ))


@send_typing_action
@admin_only_command
@handler_logging()
def remove_moderator(update: Update, context: CallbackContext) -> None:
    text = update.message.text.replace('/remove_mod ', '')
    if text == '':
        update.message.reply_text(static_text.remove_mod_usage)
        return
    u = User.get_user_by_username_or_user_id(text)
    if u is None:
        update.message.reply_text(static_text.CANT_FIND_USER_WITH_NAME_OR_ID.format(
            username_or_id=text
        ))
        return
    u.is_moderator = False
    u.save()
    update.message.reply_text(static_text.MODERATOR_REMOVED.format(
        mod_name=u.tg_str
    ))


@send_typing_action
@admin_only_command
@handler_logging()
def give_access(update: Update, context: CallbackContext) -> str:
    user_tag = update.message.text.split('@')
    if len(user_tag) != 2:
        update.message.reply_text('Usage: /gaccess @{tg_username}')
        return ConversationHandler.END
    user_tag = user_tag[1]
    user_to_give = User.get_user_by_username_or_user_id(user_tag)
    if user_to_give is None:
        update.message.reply_text(f'User @{user_tag} never messaged the bot or doesn\'t exist')
        return ConversationHandler.END
    update.message.reply_text('На сколько времени дать солюшен?', reply_markup=keyboard.admin_sub_dates_keyboard())
    context.user_data['user_to_give_access_to'] = user_tag
    return 'give_access_get_time'


@send_typing_action
@admin_only_command
@handler_logging()
def continue_giving_access(update: Update, context: CallbackContext) -> str:
    user_tag = context.user_data['user_to_give_access_to']
    del context.user_data['user_to_give_access_to']
    u = User.get_user_by_username_or_user_id(user_tag)
    if update.message.text == one_month_admin_subdate:
        u.subscription_end = datetime.now() + timedelta(days=30)
    elif update.message.text == three_month_admin_subdate:
        u.subscription_end = datetime.now() + timedelta(days=90)
    elif update.message.text == year_admin_subdate:
        u.subscription_end = datetime.now() + timedelta(days=365)
    elif update.message.text == forever_admin_subdate:
        u.subscription_end = datetime.now() + timedelta(days=36500)
    else:
        update.message.reply_text('Не воспринимаю этот текст')
        return ConversationHandler.END
    u.has_subscription = True
    u.save()
    update.message.reply_text(f"Доступ на <b>{update.message.text}</b> успешно выдан пользователю {u.tg_str}",
                              parse_mode=ParseMode.HTML)
    try:
        context.bot.send_message(
            u.user_id,
            f'Доступ на <b>{update.message.text}</b> успешно выдан пользователю {u.tg_str}',
            reply_markup=keyboard.main_keyboard(u.is_admin),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        update.message.reply_text("Сообщение не отправилось, судя по всему он кинул бота в чс.")
    return ConversationHandler.END


@send_typing_action
@admin_only_command
@handler_logging()
def remove_access(update: Update, context: CallbackContext) -> None:
    user_tag = update.message.text.split('@')
    if len(user_tag) != 2:
        update.message.reply_text('юзай так: /raccess @{tg_username}')
        return
    user_tag = user_tag[1]
    user_to_give = User.get_user_by_username_or_user_id(user_tag)
    if user_to_give is None:
        update.message.reply_text(f'Юзер @{user_tag} не писал боту или не существует')
        return
    old_sub_end = user_to_give.subscription_end.strftime("%b %d %Y %H:%M:%S")
    user_to_give.subscription_end = datetime.now()
    user_to_give.has_subscription = False
    user_to_give.save()
    update.message.reply_text(f"Доступ на {old_sub_end} успешно спизжен у пользователя @{user_tag}")
    try:
        context.bot.send_message(
            user_to_give.user_id,
            f"Доступ на {old_sub_end} успешно спизжен у пользователя @{user_tag}",
            reply_markup=keyboard.not_subbed_keyboard()
        )
    except Exception:
        update.message.reply_text("(он походу в чс бота кинул кста)")


@send_typing_action
@admin_only_command
@handler_logging()
def find_user(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("Скиньте тег челика которого пробить (тип @chovash)")
    return 'find_user_get_username'


@send_typing_action
@admin_only_command
@handler_logging()
def continue_finding_user(update: Update, context: CallbackContext) -> str:
    user_tag = update.message.text.split('@')
    if len(user_tag) != 2:
        # no @ in message
        update.message.reply_text('Usage: @<tag>',
                                  reply_markup=settings_keyboard())
        return ConversationHandler.END
    user_tag = user_tag[1]
    u = User.get_user_by_username_or_user_id(user_tag)
    if u is None:
        update.message.reply_text(f'Юзер @{user_tag} не писал боту или не существует')
        return ConversationHandler.END
    update.message.reply_text(f'''Пользователь: {u.tg_str}
Дата регистрации: {u.created_at.strftime("%b %d %Y %H:%M:%S")}
Дата последней активности: {UserActionLog.objects.filter(user=u).order_by('-created_at').first().created_at.strftime("%b %d %Y %H:%M:%S")}
Подписка до: {(u.subscription_end.strftime("%b %d %Y %H:%M:%S") if u.subscription_end.year < 2025 else "навсегда")
    if u.subscription_end and u.subscription_end > datetime.now(tz=pytz.timezone("Europe/Moscow")) else "нету"}''',
                              reply_markup=settings_keyboard())

    return ConversationHandler.END
