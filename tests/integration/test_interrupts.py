from __future__ import annotations

import pytest
from langgraph.types import Command

from dlg import DLGEngine
from dlg.exceptions import CheckpointerMissingError


def _interrupt_config() -> dict:
    return {
        "graph_id": "interrupt_test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "checkpointer": {"type": "memory"},
        "nodes": [
            {
                "name": "prepare",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            },
            {
                "name": "review",
                "handler": {
                    "module_path": "tests.helpers.interrupt_nodes",
                    "function_name": "human_review_node",
                },
                "interrupt_before": True,
            },
        ],
        "edges": {
            "entry_point": "prepare",
            "static_edges": [
                {"from": "prepare", "to": "review"},
                {"from": "review", "to": "__end__"},
            ],
        },
    }


async def test_graph_pauses_before_interrupt_node() -> None:
    graph = DLGEngine(_interrupt_config()).build()
    cfg = {"configurable": {"thread_id": "interrupt-1"}}

    result = await graph.ainvoke({"message": "hello", "result": ""}, config=cfg)
    snapshot = graph.get_state(cfg)
    assert snapshot.next == ("review",)


async def test_resume_with_command_completes() -> None:
    graph = DLGEngine(_interrupt_config()).build()
    cfg = {"configurable": {"thread_id": "interrupt-2"}}

    await graph.ainvoke({"message": "hello", "result": ""}, config=cfg)
    result = await graph.ainvoke(Command(resume="approved"), config=cfg)
    assert result["result"] == "Decision: approved"


async def test_checkpointer_missing_raises() -> None:
    cfg = {
        "graph_id": "no_checkpointer",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "nodes": [
            {
                "name": "review",
                "handler": {
                    "module_path": "tests.helpers.interrupt_nodes",
                    "function_name": "human_review_node",
                },
                "interrupt_before": True,
            }
        ],
        "edges": {
            "entry_point": "review",
            "static_edges": [{"from": "review", "to": "__end__"}],
        },
    }
    with pytest.raises(CheckpointerMissingError) as exc_info:
        DLGEngine(cfg).build()
    assert exc_info.value.context["operation"] == "interrupt"
