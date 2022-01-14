from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.handlers.utils import static_text
from tgbot.handlers.general.static_text import (
    contact_button_text, nitro_service_button_text,
    token_spammer_button_text, token_checker_button_text,
    proxy_service_button_text, buy_subscription_button_text,
    cancel_button_action, admin_command_button_text
)
from tgbot.models import User


def main_keyboard(is_admin: bool) -> ReplyKeyboardMarkup:
    buttons = [
        [
            token_spammer_button_text,
            token_checker_button_text,
            nitro_service_button_text
        ],
        [
            contact_button_text,
            proxy_service_button_text
        ]
    ]
    if is_admin:
        buttons[1].append(admin_command_button_text)
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def main_keyboard_by_user_status(user: User) -> ReplyKeyboardMarkup:
    if user.has_subscription:
        return main_keyboard(user.is_admin)
    return not_subbed_keyboard()


def settings_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            static_text.find_user_by_username_button_text,
            'Рестарт (!не работает!)',
            static_text.broadcast_message_button_text,
        ],
        [
            static_text.go_back_button_text
        ]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def sub_dates_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            'Месяц — 500 ₽',
            '3 месяца — 1000 ₽',
            'Год — 3000 ₽'
        ]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def admin_sub_dates_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            static_text.one_month_admin_subdate,
            static_text.three_month_admin_subdate,
            static_text.year_admin_subdate
        ],
        [
            static_text.forever_admin_subdate,
            cancel_button_action
        ]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def not_subbed_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            buy_subscription_button_text,
            '*пример подписки*'
        ],
        [
            contact_button_text
        ]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def cancel_keyboard():
    return ReplyKeyboardMarkup.from_button(cancel_button_action, one_time_keyboard=True, resize_keyboard=True)


def proxy_buttons(user: User, has_private_proxies: bool):
    proxy_buttons_list = [[static_text.upload_user_proxy_button_text], [cancel_button_action]]
    if user and user.is_admin:
        proxy_buttons_list[0].append(static_text.settings_admin_proxy_button_text)
    if has_private_proxies:
        proxy_buttons_list[0].append(static_text.delete_all_private_proxies)
    if (not user or (user and not user.is_admin)) and not has_private_proxies:
        proxy_buttons_list = [[static_text.upload_user_proxy_button_text, cancel_button_action]]
    return ReplyKeyboardMarkup(proxy_buttons_list, one_time_keyboard=True, resize_keyboard=True)


def proxy_type():
    proxy_types = [['socks4', 'socks5', 'http'], [cancel_button_action]]
    return ReplyKeyboardMarkup(proxy_types, one_time_keyboard=True, resize_keyboard=True)


def admin_proxy_keyboard():
    buttons = [[static_text.upload_proxy_admin_button_text, static_text.export_public_proxy_button_text],
               [cancel_button_action]]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def remove_reply_keyboard():
    return ReplyKeyboardRemove()


def cancel_message_button_keyboard(callback_data):
    buttons = [[InlineKeyboardButton(cancel_button_action, callback_data=callback_data)]]
    return InlineKeyboardMarkup(buttons)


def remove_inline_keyboard():
    return InlineKeyboardMarkup([[]])
