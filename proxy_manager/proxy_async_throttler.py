import asyncio
import time
from collections import deque

from django.core.cache import cache
from typing import List

from dtb.settings import DEFAULT_THROTTLER_RATE_LIMIT, DEFAULT_THROTTLER_PERIOD
from proxy_manager.models import Proxy


class ProxyDoesNotExistException(Exception):
    pass


class ProxyAsyncThrottler:
    def __init__(
            self, proxy_id: int = None, cache_key: str = None,
            rate_limit: float = DEFAULT_THROTTLER_RATE_LIMIT,
            period: float = DEFAULT_THROTTLER_PERIOD
    ):
        self._proxy_id = proxy_id
        if cache_key is None and cache_key is None:
            raise ValueError('You have to specify one of the two arguments')
        elif cache_key is None:
            self._cache_key = f'throttler_{self._proxy_id}_task_logs'
        else:
            self._cache_key = cache_key
        self._task_logs = cache.get_or_set(self._cache_key, deque())

        self.rate_limit = rate_limit
        self.period = period
        self.retry_interval = 0.01

    def task_logs_append(self, value):
        task_logs = cache.get(self._cache_key)
        task_logs.append(value)
        cache.set(self._cache_key, task_logs)

    def _task_logs_update(self):
        self._task_logs = cache.get(self._cache_key)

    def _task_logs_popleft(self):
        self._task_logs.popleft()
        cache.set(self._cache_key, self._task_logs)

    def flush(self):
        now = time.monotonic()
        self._task_logs_update()
        while self._task_logs:
            if self._task_logs and now - self._task_logs[0] > self.period:
                self._task_logs_popleft()
            else:
                break
            self._task_logs_update()

    async def acquire(self):
        while True:
            self.flush()
            if len(self._task_logs) < self.rate_limit:
                break
            await asyncio.sleep(self.retry_interval)

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    # @classmethod
    # def clear_cache_for_proxies(cls, proxy_list: List[Proxy]):
    #     for i in proxy_list:
    #         cache.delete(f'proxy_throttler_{i.pk}_task_logs')
