from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph
from tests.helpers.simple_state import SimpleState


def subgraph_echo(state: dict[str, Any]) -> dict[str, Any]:
    return {"result": f"Sub: {state['message']}"}


def _build_subgraph() -> Any:
    g = StateGraph(SimpleState)
    g.add_node("sub_echo", subgraph_echo)
    g.set_entry_point("sub_echo")
    g.add_edge("sub_echo", "__end__")
    return g.compile()


compiled_subgraph = _build_subgraph()
