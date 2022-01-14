import asyncio
import datetime
from typing import Dict, Optional

import aiohttp
from channels.db import database_sync_to_async
from django.utils import timezone
from telegram import ParseMode

from dtb.celery import app
from dtb.settings import MINUTES_TO_CHECK_PUBLIC_PROXY
from proxy_manager.models import Proxy
from tgbot.handlers.proxy_add_delete import static_text
from tgbot.handlers.utils import keyboard
from tgbot.models import User


@app.task(ignore_result=True)
def ping_proxies(proxy_dict: Dict[str, str], timeout: int, start_time: datetime.datetime,
                 tg_id_notify: Optional[int] = None, owner: Optional[User] = None):
    asyncio.run(async_proxy_ping(proxy_dict, timeout, start_time, tg_id_notify, owner))


async def async_proxy_ping(proxy_dict: Dict[str, str], timeout: int, start_time: datetime.datetime,
                           tg_id_notify: Optional[int] = None, owner: Optional[User] = None):
    counter, working_proxy_count, dead_proxy_count = 0, 0, 0
    from tgbot.dispatcher import bot
    task_list = []
    for k, v in proxy_dict.items():
        task_list.append(asyncio.create_task(check_proxy(k, timeout)))
    for i in task_list:
        res = await i
        if res[0]:
            await database_sync_to_async(Proxy.objects.update_or_create)(owner=owner, is_public=owner is None,
                                                                         proxy_scheme='http', proxy_url=res[1])
            working_proxy_count += 1
        else:
            dead_proxy_count += 1
    if tg_id_notify:
        bot.send_message(
            chat_id=tg_id_notify,
            text=f'✅ <b>Готово! ({str((timezone.now() - start_time).total_seconds())[:-4]} секунд)</b>\n'
                 f'Чекнул <code>{working_proxy_count + dead_proxy_count}</code> прокси!\n'
                 f'Из них <code>{working_proxy_count}</code> рабочие и <code>{dead_proxy_count}</code> мертвы.',
            parse_mode=ParseMode.HTML,
        )
        if owner is None:
            text = static_text.admin_proxy_information_text(working_proxy_count + dead_proxy_count, working_proxy_count)
        else:
            text = static_text.user_private_proxy_information_text(working_proxy_count, MINUTES_TO_CHECK_PUBLIC_PROXY)
        bot.send_message(
            chat_id=tg_id_notify,
            text=text,
            reply_markup=keyboard.proxy_buttons(owner, True),
            parse_mode=ParseMode.HTML
        )



async def check_proxy(proxy_url, timeout):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://google.com', timeout=timeout, proxy=f'http://{proxy_url}',
                                   allow_redirects=False) as resp:
                return True, proxy_url
    except Exception:
        return False, proxy_url
