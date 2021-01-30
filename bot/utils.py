import asyncio


async def _run_with_delay(delay: float, coroutine):
    await asyncio.sleep(delay)
    return await coroutine


async def run_task_with_delay(delay: float, coroutine):
    asyncio.create_task(_run_with_delay(delay, coroutine))
