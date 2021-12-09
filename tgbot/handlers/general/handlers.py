from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from tgbot.handlers.general import static_text
from tgbot.handlers.utils.decorators import handler_logging


@handler_logging()
def start(update: Update, context: CallbackContext) -> None:
    """ /start command """

    update.message.reply_text(
        static_text.start_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@handler_logging()
def help_command(update: Update, context: CallbackContext) -> None:
    """ /help command """

    update.message.reply_text(
        static_text.help_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@handler_logging()
def contact(update: Update, context: CallbackContext) -> None:
    """ /contact command """

    update.message.reply_text(
        static_text.contact_command,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

