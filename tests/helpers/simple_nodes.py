from __future__ import annotations

from typing import Any


def echo_node(state: dict[str, Any]) -> dict[str, Any]:
    return {"result": f"Echo: {state['message']}"}


async def async_echo_node(state: dict[str, Any]) -> dict[str, Any]:
    return {"result": f"Echo: {state['message']}"}
