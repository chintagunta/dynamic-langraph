from __future__ import annotations

import pytest

from dlg._config import NodeConfig, RetryPolicyConfig
from dlg._wrappers import create_async_wrapper


def _node_cfg(name: str = "n", **kwargs: object) -> NodeConfig:
    base = {"name": name, "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}}
    base.update(kwargs)
    return NodeConfig.model_validate(base)


async def test_retry_then_succeed() -> None:
    call_count = 0

    async def flaky(state: dict) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("temporary error")
        return {"result": "ok"}

    cfg = _node_cfg(
        retry_policy={"max_attempts": 3, "initial_interval": 0.001, "backoff_factor": 1.0},
    )
    wrapped = create_async_wrapper(cfg, flaky)
    result = await wrapped({"message": "hi"})
    assert result == {"result": "ok"}
    assert call_count == 3


async def test_exhausted_retries_with_fallback() -> None:
    async def always_fail(state: dict) -> dict:
        raise RuntimeError("always fails")

    cfg = _node_cfg(
        retry_policy={"max_attempts": 2, "initial_interval": 0.001, "backoff_factor": 1.0},
        fallback_node="fallback",
    )
    wrapped = create_async_wrapper(cfg, always_fail)
    result = await wrapped({"message": "hi"})
    # Should return Command with goto=fallback
    from langgraph.types import Command
    assert isinstance(result, Command)


async def test_exhausted_retries_without_fallback_raises() -> None:
    async def always_fail(state: dict) -> dict:
        raise ValueError("no fallback")

    cfg = _node_cfg(
        retry_policy={"max_attempts": 2, "initial_interval": 0.001, "backoff_factor": 1.0},
    )
    wrapped = create_async_wrapper(cfg, always_fail)
    with pytest.raises(ValueError, match="no fallback"):
        await wrapped({"message": "hi"})
