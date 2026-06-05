from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Callable

from langgraph.types import Send

from dlg._config import NodeConfig
from dlg.exceptions import NodeTimeoutException


def create_async_wrapper(
    node_config: NodeConfig,
    handler_fn: Callable[..., Any],
) -> Callable[..., Any]:
    is_async = inspect.iscoroutinefunction(handler_fn)
    node_name = node_config.name
    timeout = node_config.timeout_seconds
    retry_policy = node_config.retry_policy
    fallback_node = node_config.fallback_node

    max_attempts = retry_policy.max_attempts if retry_policy else 1
    initial_interval = retry_policy.initial_interval if retry_policy else 1.0
    backoff_factor = retry_policy.backoff_factor if retry_policy else 2.0

    async def wrapper(state: Any, *args: Any, **kwargs: Any) -> Any:
        attempt = 0
        interval = initial_interval
        last_exc: Exception | None = None

        while attempt < max_attempts:
            attempt += 1
            try:
                start = time.monotonic()
                if is_async:
                    coro = handler_fn(state, *args, **kwargs)
                else:
                    # Run sync handler directly to preserve LangGraph contextvars
                    # (run_in_executor drops context, breaking interrupt() support)
                    async def _sync_to_async() -> Any:
                        return handler_fn(state, *args, **kwargs)

                    coro = _sync_to_async()

                if timeout is not None:
                    try:
                        result = await asyncio.wait_for(coro, timeout=timeout)
                    except asyncio.TimeoutError:
                        elapsed = time.monotonic() - start
                        raise NodeTimeoutException(
                            f"Node '{node_name}' timed out after {elapsed:.3f}s",
                            {"node_name": node_name, "timeout_seconds": timeout, "elapsed_seconds": elapsed},
                        )
                else:
                    result = await coro

                if isinstance(result, list) and result and isinstance(result[0], Send):
                    return result

                return result

            except NodeTimeoutException:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts:
                    await asyncio.sleep(interval)
                    interval *= backoff_factor

        if fallback_node and last_exc is not None:
            from langgraph.types import Command
            return Command(goto=fallback_node, update={"error_log": str(last_exc)})

        if last_exc is not None:
            raise last_exc

        return {}

    return wrapper
