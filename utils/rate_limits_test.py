import asyncio
import datetime

import aiohttp
import random

import requests
from asyncio_throttle import Throttler

from utils.discord_response import DiscordResponse

counter = {}
start = None


def print_counter():
    print(
        f'across {len(counter.keys())} tokens we did {sum([len(v["200"]) + len(v["401"]) + len(v["other"]) for v in counter.values()])} requests')
    print(f'time: {datetime.datetime.now().timestamp() - start.timestamp()}')

    def in_last_x_seconds(seconds):
        _200 = sum([len([j for j in v["200"] if datetime.datetime.now().timestamp() - seconds < j.timestamp()]) for v in
                    counter.values()])
        _401 = sum([len([j for j in v["401"] if datetime.datetime.now().timestamp() - seconds < j.timestamp()]) for v in
                    counter.values()])
        _other = sum(
            [len([j for j in v["other"] if datetime.datetime.now().timestamp() - seconds < j.timestamp()]) for v in
             counter.values()])
        print(f'in last {seconds} second(s):\n'
              f'200: {_200}\n'
              f'401: {_401}\n'
              f'total: {_200 + _401 + _other}\n')
        if _other != 0:
            raise ValueError()

    in_last_x_seconds(0.3)
    in_last_x_seconds(1)
    in_last_x_seconds(2)
    in_last_x_seconds(5)
    in_last_x_seconds(10)
    in_last_x_seconds(15)


rcounter = 0


async def request(method: str, url: str, proxy: str, throttler: Throttler, proxy_index, **kwargs) -> DiscordResponse:
    async with aiohttp.ClientSession() as session:
        async with throttler:
            try:
                async with session.request(method, url, timeout=10, allow_redirects=False, proxy='http://pFirEp:vrVaeSfEei@109.248.14.86:3000', **kwargs) as resp:
                    global counter, rcounter
                    rcounter += 1
                    print(f'[{datetime.datetime.now().strftime("%X.%f")}] request {rcounter} (current req/sec: {rcounter / (datetime.datetime.now().timestamp() - start.timestamp())})')
                    if resp.status == 429:
                        raise ValueError(f'429')
                    if counter.get(kwargs['headers']['authorization']) is None:
                        counter[kwargs['headers']['authorization']] = {'200': [], '401': [], 'other': []}
                    if resp.status == 200:
                        counter[kwargs['headers']['authorization']]['200'].append(datetime.datetime.now())
                    elif resp.status == 401:
                        counter[kwargs['headers']['authorization']]['401'].append(datetime.datetime.now())
                    else:
                        counter[kwargs['headers']['authorization']]['other'].append(datetime.datetime.now())
                    response_object = DiscordResponse(await resp.json(), resp.status, resp.headers,
                                                      kwargs['headers']['authorization'])
                    return response_object
            except asyncio.exceptions.TimeoutError as e:
                print('timeout')
                # print_counter()


async def main():
    token_list = open('tokens_for_test.txt', 'r').read().split('\n')
    task_list = []

    url_list = [
        'https://discord.com/api/users/@me',
    ]
    proxy_list = [
    ]
    throttler_list = [Throttler(28, 1) for i in range(1)]
    proxy_index = 0
    for i in range(10000):
        random_token = random.choice(token_list)
        random_url = random.choice(url_list)

        task_list.append(asyncio.create_task(request(
            'get', random_url, 'proxy_list[proxy_index]', throttler_list[proxy_index], 'proxy_list.index(proxy)',
            headers={'authorization': random_token}
        )))
    global start
    start = datetime.datetime.now()
    result = set()
    for i in task_list:
        res = await i
        if res.ok():
            result.add(res.token)
    print('\n'.join([str(i) for i in result]))


if __name__ == '__main__':
    asyncio.run(main())
