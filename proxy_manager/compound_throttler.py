import time

from proxy_manager.proxy_async_throttler import ProxyAsyncThrottler


class CompoundThrottler:
    """ includes 3 async throttlers - per-proxy (total request count), per-proxy (invalid request count), per-token """

    def __init__(self, proxy_id):
        self.__per_proxy_total = ProxyAsyncThrottler(cache_key=f'per_proxy_total_throttler__{proxy_id}')
        self.__per_proxy_invalid = ProxyAsyncThrottler(cache_key=f'per_proxy_invalid_throttler__{proxy_id}', rate_limit=10000, period=600)
        # self.__per_token = ProxyAsyncThrottler(cache_key=f'per_token_throttler__{token}', rate_limit=5, period=5)

    def add_invalid_request(self):
        """ call whenever there's an invalid request to api """
        self.__per_proxy_invalid.task_logs_append(time.monotonic())

    async def acquire(self):
        # await self.__per_token.acquire()
        # self.__per_token.task_logs_append(time.monotonic())
        await self.__per_proxy_total.acquire()
        self.__per_proxy_total.task_logs_append(time.monotonic())
        await self.__per_proxy_invalid.acquire()

    def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

