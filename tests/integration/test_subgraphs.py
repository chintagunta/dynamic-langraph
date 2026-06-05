from __future__ import annotations

import pytest

from dlg.compiler import DLGCompiler


def _subgraph_parent_config() -> dict:
    return {
        "graph_id": "subgraph_parent",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "nodes": [
            {
                "name": "sub_node",
                "subgraph": {
                    "module_path": "tests.helpers.subgraph_module",
                    "graph_name": "compiled_subgraph",
                },
            }
        ],
        "edges": {
            "entry_point": "sub_node",
            "static_edges": [{"from": "sub_node", "to": "__end__"}],
        },
    }


async def test_subgraph_executes_as_node() -> None:
    graph = DLGCompiler(_subgraph_parent_config()).compile()
    result = await graph.ainvoke({"message": "hello", "result": ""})
    assert result["result"] == "Sub: hello"
