from datetime import timedelta

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.admin import static_text
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
from tgbot.handlers.utils.decorators import mod_only_command, admin_only_command, handler_logging
from tgbot.models import User


@mod_only_command
@handler_logging()
def admin(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    update.message.reply_text(static_text.secret_admin_commands)


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


@admin_only_command
@handler_logging()
def export_users(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)

    # in values argument you can specify which fields should be returned in output csv
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    update.message.reply_document(document=csv_users)


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
