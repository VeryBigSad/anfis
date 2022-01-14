import asyncio
from asyncio import Task


class TaskPool:
    def __init__(self, workers: int) -> None:
        self._semaphore = asyncio.Semaphore(workers)
        self._tasks = set()

    async def put(self, coro) -> None:
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