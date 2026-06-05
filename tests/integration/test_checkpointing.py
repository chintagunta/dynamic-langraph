from __future__ import annotations

import pytest

from dlg import DLGEngine


def _checkpoint_config() -> dict:
    return {
        "graph_id": "checkpoint_test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "checkpointer": {"type": "memory"},
        "nodes": [
            {
                "name": "echo",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            }
        ],
        "edges": {
            "entry_point": "echo",
            "static_edges": [{"from": "echo", "to": "__end__"}],
        },
    }


async def test_state_persists_across_invocations() -> None:
    graph = DLGEngine(_checkpoint_config()).build()
    cfg = {"configurable": {"thread_id": "thread-1"}}
    result1 = await graph.ainvoke({"message": "first", "result": ""}, config=cfg)
    assert result1["result"] == "Echo: first"

    result2 = await graph.ainvoke({"message": "second", "result": ""}, config=cfg)
    assert result2["result"] == "Echo: second"


async def test_get_state_returns_snapshot() -> None:
    graph = DLGEngine(_checkpoint_config()).build()
    cfg = {"configurable": {"thread_id": "thread-snapshot"}}
    await graph.ainvoke({"message": "hello", "result": ""}, config=cfg)
    snapshot = graph.get_state(cfg)
    assert snapshot is not None
    assert snapshot.values["result"] == "Echo: hello"


async def test_get_state_history_returns_list() -> None:
    graph = DLGEngine(_checkpoint_config()).build()
    cfg = {"configurable": {"thread_id": "thread-history"}}
    await graph.ainvoke({"message": "hello", "result": ""}, config=cfg)
    history = list(graph.get_state_history(cfg))
    assert len(history) >= 1
