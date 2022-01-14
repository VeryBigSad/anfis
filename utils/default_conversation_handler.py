from typing import Callable

from telegram import Update
from telegram.bot import RT
from telegram.ext import ConversationHandler, MessageHandler, Filters, CommandHandler, BaseFilter
from telegram.ext.utils.types import CCT

from tgbot.handlers.general import handlers as general_handlers
from tgbot.handlers.general.static_text import cancel_button_action


def get_conv_handler(
        entry_point_button_text: str, entry_point_func: Callable[[Update, CCT], RT],
        state_str: str, state_filter: BaseFilter, state_func: Callable[[Update, CCT], RT]
) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex(f'^{entry_point_button_text}$'), entry_point_func)],
        states={
            state_str: [
                MessageHandler(
                    state_filter,
                    state_func
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.regex(f'^{cancel_button_action}$'), general_handlers.cancel),
                   CommandHandler('cancel', general_handlers.cancel)]
    )
