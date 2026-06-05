from __future__ import annotations

import asyncio
from typing import Any, Callable

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph


class DLGTestHarness:
    @staticmethod
    def test_node(
        handler_fn: Callable[..., Any],
        state_dict: dict[str, Any],
        *,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return asyncio.run(DLGTestHarness.atest_node(handler_fn, state_dict, config=config))

    @staticmethod
    async def atest_node(
        handler_fn: Callable[..., Any],
        state_dict: dict[str, Any],
        *,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from typing_extensions import TypedDict

        fields = {k: Any for k in state_dict}
        StateClass = TypedDict("_DynamicState", {k: Any for k in state_dict})  # type: ignore[misc]

        graph = StateGraph(StateClass)
        graph.add_node("node", handler_fn)
        graph.set_entry_point("node")
        graph.add_edge("node", "__end__")

        compiled = graph.compile(checkpointer=InMemorySaver())
        result = await compiled.ainvoke(state_dict, config=config or {"configurable": {"thread_id": "test"}})
        return {k: result[k] for k in result if result[k] != state_dict.get(k)}

    @staticmethod
    def assert_state_delta(
        result: dict[str, Any],
        expected: dict[str, Any],
    ) -> None:
        for key, value in expected.items():
            assert key in result, f"Key '{key}' not in result delta"
            assert result[key] == value, f"Expected result['{key}'] == {value!r}, got {result[key]!r}"
