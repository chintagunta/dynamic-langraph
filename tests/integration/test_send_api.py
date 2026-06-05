from __future__ import annotations

import pytest

from dlg import DLGEngine


def _fanout_config() -> dict:
    return {
        "graph_id": "fanout_test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.fanout_state",
            "class_name": "FanOutState",
        },
        "nodes": [
            {
                "name": "fan_out",
                "handler": {
                    "module_path": "tests.helpers.fanout_nodes",
                    "function_name": "fan_out_passthrough",
                },
                "send_api": True,
            },
            {
                "name": "process_item",
                "handler": {
                    "module_path": "tests.helpers.fanout_nodes",
                    "function_name": "process_item_node",
                },
            },
        ],
        "edges": {
            "entry_point": "fan_out",
            "conditional_edges": [
                {
                    "from": "fan_out",
                    "send_router": {
                        "module_path": "tests.helpers.fanout_nodes",
                        "function_name": "fan_out_router",
                    },
                }
            ],
            "static_edges": [{"from": "process_item", "to": "__end__"}],
        },
    }


async def test_fanout_dispatches_parallel_branches() -> None:
    graph = DLGEngine(_fanout_config()).build()
    result = await graph.ainvoke({"items": ["a", "b", "c"], "results": []})
    assert sorted(result["results"]) == ["A", "B", "C"]
