from __future__ import annotations

import asyncio

import pytest

from dlg._wrappers import create_async_wrapper
from dlg._config import NodeConfig


def _node_config(**kwargs: object) -> NodeConfig:
    base = {
        "name": "test_node",
        "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"},
    }
    base.update(kwargs)
    return NodeConfig.model_validate(base)


async def test_sync_handler_wraps_to_async() -> None:
    def sync_fn(state: dict) -> dict:
        return {"result": "sync"}

    wrapped = create_async_wrapper(_node_config(), sync_fn)
    result = await wrapped({"message": "hello"})
    assert result == {"result": "sync"}


async def test_async_handler_passes_through() -> None:
    async def async_fn(state: dict) -> dict:
        return {"result": "async"}

    wrapped = create_async_wrapper(_node_config(), async_fn)
    result = await wrapped({"message": "hello"})
    assert result == {"result": "async"}


async def test_timeout_raises_node_timeout() -> None:
    from dlg.exceptions import NodeTimeoutException

    async def slow_fn(state: dict) -> dict:
        await asyncio.sleep(10)
        return {}

    cfg = _node_config(timeout_seconds=0.05)
    wrapped = create_async_wrapper(cfg, slow_fn)
    with pytest.raises(NodeTimeoutException) as exc_info:
        await wrapped({"message": "hello"})
    assert exc_info.value.context["node_name"] == "test_node"


async def test_send_list_passthrough() -> None:
    from langgraph.types import Send

    async def send_fn(state: dict) -> list:
        return [Send("target", {"x": 1})]

    cfg = _node_config(send_api=True)
    wrapped = create_async_wrapper(cfg, send_fn)
    result = await wrapped({"message": "hello"})
    assert isinstance(result, list)
    assert isinstance(result[0], Send)
