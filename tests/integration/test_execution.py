from __future__ import annotations

import time

import pytest

from dlg import DLGEngine


def _minimal_config() -> dict:
    return {
        "graph_id": "exec_test",
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


async def test_minimal_config_ainvoke() -> None:
    graph = DLGEngine.from_file  # just validate the class exists
    graph = DLGEngine(_minimal_config()).build()
    result = await graph.ainvoke({"message": "hello", "result": ""})
    assert result["result"] == "Echo: hello"


async def test_sync_handler_completes_under_5s() -> None:
    graph = DLGEngine(_minimal_config()).build()
    start = time.monotonic()
    result = await graph.ainvoke({"message": "timing", "result": ""})
    elapsed = time.monotonic() - start
    assert result["result"].startswith("Echo:")
    assert elapsed < 5.0


async def test_abatch_two_inputs() -> None:
    graph = DLGEngine(_minimal_config()).build()
    results = await graph.abatch([
        {"message": "first", "result": ""},
        {"message": "second", "result": ""},
    ])
    assert results[0]["result"] == "Echo: first"
    assert results[1]["result"] == "Echo: second"


async def test_draw_ascii_or_mermaid() -> None:
    graph = DLGEngine(_minimal_config()).build()
    # draw_ascii requires grandalf; fall back to mermaid if not installed
    try:
        diagram = graph.get_graph().draw_ascii()
        assert isinstance(diagram, str) and len(diagram) > 0
    except ImportError:
        diagram = graph.get_graph().draw_mermaid()
        assert isinstance(diagram, str) and len(diagram) > 0


async def test_async_handler_executes() -> None:
    cfg = _minimal_config()
    cfg["nodes"][0]["handler"]["function_name"] = "async_echo_node"
    graph = DLGEngine(cfg).build()
    result = await graph.ainvoke({"message": "async test", "result": ""})
    assert result["result"] == "Echo: async test"
