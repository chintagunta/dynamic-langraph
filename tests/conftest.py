from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import InMemorySaver


@pytest.fixture
def in_memory_saver() -> InMemorySaver:
    return InMemorySaver()


@pytest.fixture
def echo_handler():
    def handler(state: dict) -> dict:  # type: ignore[type-arg]
        return {"result": f"Echo: {state['message']}"}

    return handler


@pytest.fixture
def simple_graph_config() -> dict:  # type: ignore[type-arg]
    return {
        "graph_id": "test_graph",
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
