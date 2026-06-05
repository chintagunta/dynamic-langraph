from __future__ import annotations

import pytest

from dlg import DLGEngine


def _minimal_config() -> dict:
    return {
        "graph_id": "stream_test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
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


async def test_stream_updates_emits_one_event_per_node() -> None:
    graph = DLGEngine(_minimal_config()).build()
    events = []
    async for event in graph.astream({"message": "hello", "result": ""}, stream_mode="updates"):
        events.append(event)
    assert len(events) == 1
    assert "echo" in events[0]


async def test_stream_values_emits_cumulative_state() -> None:
    graph = DLGEngine(_minimal_config()).build()
    events = []
    async for event in graph.astream({"message": "hello", "result": ""}, stream_mode="values"):
        events.append(event)
    assert len(events) >= 1
    last = events[-1]
    assert last["result"] == "Echo: hello"
