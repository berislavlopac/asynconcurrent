import asyncio
import logging

log = logging.getLogger(__name__)


class TaskPoolExecutor:
    def __init__(self, max_size, collect_results=False):
        self._semaphore = asyncio.Semaphore(max_size)
        self._tasks = set()
        self.results = [] if collect_results else None

    async def submit(self, coro, *args, **kwargs):
        await self._semaphore.acquire()
        if asyncio.iscoroutinefunction(coro):
            coro = coro(*args, **kwargs)
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)
        return task

    async def map(self, coro, *iterables, timeout=None):
        tasks = [await self.submit(coro, *args) for args in zip(*iterables)]
        tasks.reverse()
        for task in asyncio.as_completed(tasks, timeout=timeout):
            yield await task

    async def shutdown(self, *, wait=True):
        if self._tasks:
            if wait:
                await asyncio.wait(self._tasks)
            else:
                for task in self._tasks:
                    task.cancel()

    def _on_task_done(self, task):
        exception = task.exception()
        result = task.result()
        self._tasks.remove(task)
        self._semaphore.release()
        if self.results is not None:
            log.info(f"task done: {result}")
            self.results.append(exception or result)
        elif exception:
            raise exception

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()
        return False
