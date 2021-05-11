import asyncio
from random import randint
from time import perf_counter

import pytest

from asynconcurrent.futures import TaskPoolExecutor


@pytest.fixture
def timeouts():
    return [randint(0, 3) for _ in range(10)]


async def process(number, sleep_time):
    start = perf_counter()
    await asyncio.sleep(sleep_time)
    elapsed = perf_counter() - start
    assert elapsed == pytest.approx(sleep_time, rel=1e-2, abs=1e-3)
    return number, sleep_time


@pytest.mark.asyncio
async def test_submit(timeouts):
    start = perf_counter()
    async with TaskPoolExecutor(max_size=4, collect_results=True) as executor:
        for result, sleep_time in enumerate(timeouts):
            await executor.submit(process, result, sleep_time)
    elapsed = perf_counter() - start
    assert elapsed < sum(timeouts)
    assert sorted(executor.results) == sorted(enumerate(timeouts))


@pytest.mark.asyncio
async def test_map(timeouts):
    results = []
    start = perf_counter()
    async with TaskPoolExecutor(max_size=4) as executor:
        async for result in executor.map(process, *zip(*enumerate(timeouts))):
            results.append(result)
    elapsed = perf_counter() - start
    assert elapsed < sum(timeouts)
    assert sorted(results) == sorted(enumerate(timeouts))
