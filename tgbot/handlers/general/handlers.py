import time

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler

from tgbot.handlers.general import static_text
from tgbot.handlers.utils.decorators import handler_logging, send_typing_action
from tgbot.handlers.utils.keyboard import main_keyboard, not_subbed_keyboard, main_keyboard_by_user_status
from tgbot.models import User


@send_typing_action
@handler_logging()
def start(update: Update, context: CallbackContext) -> None:
    """ /start command """
    u = User.get_user(update, context)
    if u.has_subscription:
        update.message.reply_text(
            static_text.subbed_start_command(u.tg_str, u.user_id),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=main_keyboard(u.is_admin)
        )
    else:
        update.message.reply_text(
            static_text.unsubbed_start_command(u.tg_str, u.user_id),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=not_subbed_keyboard()
        )
    return ConversationHandler.END


@send_typing_action
@handler_logging()
def help_command(update: Update, context: CallbackContext) -> None:
    """ /help command """
    u = User.get_user(update, context)

    update.message.reply_text(
        static_text.help_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard_by_user_status(u)
    )


@send_typing_action
@handler_logging()
def contact(update: Update, context: CallbackContext) -> None:
    """ /contact command """
    u = User.get_user(update, context)

    update.message.reply_text(
        static_text.contact_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard_by_user_status(u)
    )


@send_typing_action
@handler_logging()
def cancel(update: Update, context: CallbackContext) -> str:
    """ /cancel command (or text!) """
    u = User.get_user(update, context)

    update.message.reply_text(
        static_text.cancel_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard_by_user_status(u)
    )
    return ConversationHandler.END


@send_typing_action
@handler_logging()
def buy_subscription(update: Update, context: CallbackContext) -> None:
    """ хуйня для покупки подписки """
    u = User.get_user(update, context)
    # TODO: finish off
    update.message.reply_text(
        static_text.buy_subscription_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=main_keyboard_by_user_status(u)
    )


@send_typing_action
@handler_logging()
def go_back(update: Update, context: CallbackContext):
    """ вернуться в главное меню """
    start(update, context)
    return ConversationHandler.END
