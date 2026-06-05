from __future__ import annotations

from typing import Any

from langgraph.types import Send


def fan_out_passthrough(state: dict[str, Any]) -> dict[str, Any]:
    return {}


def fan_out_router(state: dict[str, Any]) -> list[Send]:
    return [Send("process_item", {"items": [], "results": [], "_item": item}) for item in state["items"]]


def process_item_node(state: dict[str, Any]) -> dict[str, Any]:
    item = state.get("_item", "")
    return {"results": [str(item).upper()]}
