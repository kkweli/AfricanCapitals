import asyncio
from typing import Any, Callable, Coroutine, List
from functools import wraps

def async_timed():
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            start = asyncio.get_event_loop().time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = asyncio.get_event_loop().time()
                total = end - start
                print(f'{func.__name__} took {total:.2f} seconds')
        return wrapped
    return wrapper

async def gather_with_concurrency(n: int, timeout: int, *tasks) -> List[Any]:
    """
    Run tasks with limited concurrency and timeout
    """
    semaphore = asyncio.Semaphore(n)
    
    async def bounded_task(task):
        async with semaphore:
            try:
                return await asyncio.wait_for(task, timeout=timeout)
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                return None
    
    return await asyncio.gather(
        *(bounded_task(task) for task in tasks),
        return_exceptions=False
    )