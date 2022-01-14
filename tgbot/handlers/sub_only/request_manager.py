from __future__ import annotations

import asyncio
import datetime
import hashlib
import logging
import random
import aiosonic

from typing import List

from aiosonic import TCPConnector

from proxy_manager.compound_throttler import CompoundThrottler
from proxy_manager.models import Proxy
from tgbot.handlers.sub_only.exceptions import AccountDisabledError, TimeoutTooLongError, TokenDeadError
from tgbot.handlers.sub_only.task_pool import TaskPool
from utils.discord_response import DiscordResponse


class RequestManager:
    thingy = None

    def __init__(self, proxy_list: List[Proxy]):
        # TODO: make a method to update the list
        if RequestManager.thingy is None:
            RequestManager.thingy = self

        self.__task_pool_dict = {proxy: TaskPool(1) for proxy in proxy_list}
        # self.__throttler_dict = {proxy: CompoundThrottler(proxy.pk) for proxy in proxy_list}
        self.__proxy_list = proxy_list
        self.__proxy_list_counter = 0

        self.__request_queue = []
        self.__response_dict = {}
        self.__client = aiosonic.HTTPClient()

    @classmethod
    def get_instance(cls) -> RequestManager:
        if cls.thingy is not None:
            return cls.thingy
        raise ValueError('RequestManager() wasn\'t started even once!')

    async def request(self, method, url, **kwargs) -> DiscordResponse:
        """ gets information for the request, returns the request id """
        self.__proxy_list_counter = (self.__proxy_list_counter + 1) % len(self.__proxy_list)
        proxy = self.__proxy_list[self.__proxy_list_counter]

        s = self.__task_pool_dict[proxy]
        proxy_host, proxy_auth = proxy.proxy_url.split('@')[1], proxy.proxy_url.split('@')[0]
        proxy_object = aiosonic.proxy.Proxy(f'http://{proxy_host}', proxy_auth)
        client = aiosonic.HTTPClient(connector=TCPConnector(1), proxy=proxy_object)
        return await asyncio.create_task(self.__request(url, method, s, client, **kwargs))

    @staticmethod
    async def __request(url, method, pool, client: aiosonic.HTTPClient, **kwargs):
        while True:
            async with pool:
                try:
                    resp = await client.request(url, method, **kwargs)
                    if resp.status_code == 401:
                        raise TokenDeadError
                    elif resp.status_code == 403:
                        raise AccountDisabledError
                    elif resp.status_code == 429:
                        if int(resp.headers['Retry-After']) > 100:
                            raise TimeoutTooLongError
                        print(f'[{datetime.datetime.now().strftime("%X.%f")}] request 429 FUCKED')
                        await asyncio.sleep(int(resp.headers['Retry-After']))
                        continue

                    print(f'[{datetime.datetime.now().strftime("%X.%f")}] request DONE')
                    text = await resp.text()

                    return DiscordResponse(await resp.json(), resp.status_code, resp.headers)

                except aiosonic.exceptions.TimeoutException as e:
                    print(f'[{datetime.datetime.now().strftime("%X.%f")}] request TIMED OUT')
                    await asyncio.sleep(2 + random.random() * 2)

