from __future__ import annotations

from typing import Any

from langgraph.types import interrupt


def human_review_node(state: dict[str, Any]) -> dict[str, Any]:
    decision = interrupt("Approve this result?")
    return {"result": f"Decision: {decision}"}
