import asyncio
from collections.abc import Coroutine
from typing import Any

_tasks: dict[str, asyncio.Task] = {}


def run_in_background(job_id: str, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
    """Runs a worker coroutine as a fire-and-forget task in this process.

    Replaces RQ enqueueing — there's no separate worker process anymore, the
    coroutine just runs on the FastAPI event loop. The task is kept in a
    module-level dict (not just discarded) so it isn't garbage-collected
    mid-flight and so `cancel_job` can find it.
    """
    task = asyncio.create_task(coro)
    _tasks[job_id] = task
    task.add_done_callback(lambda _t: _tasks.pop(job_id, None))
    return task


def cancel_job(job_id: str) -> bool:
    task = _tasks.get(job_id)
    if task is None:
        return False
    return task.cancel()
