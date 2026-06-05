from __future__ import annotations

import pytest

from dlg.exceptions import (
    GraphValidationError,
    StaticLoopException,
    UnreachableNodeException,
)
from dlg.validator import DLGValidator


def _minimal_config() -> dict:
    return {
        "graph_id": "integration_test",
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


def test_valid_minimal_config_passes() -> None:
    DLGValidator(_minimal_config()).validate()


def test_bad_module_raises_before_graph_runs() -> None:
    cfg = _minimal_config()
    cfg["nodes"][0]["handler"]["module_path"] = "nonexistent.xyz"
    with pytest.raises(GraphValidationError) as exc_info:
        DLGValidator(cfg).validate()
    assert "nonexistent.xyz" in str(exc_info.value.context)


def test_unreachable_node_raises_correct_exception() -> None:
    cfg = _minimal_config()
    cfg["nodes"].append(
        {
            "name": "orphan",
            "handler": {
                "module_path": "tests.helpers.simple_nodes",
                "function_name": "echo_node",
            },
        }
    )
    with pytest.raises(UnreachableNodeException) as exc_info:
        DLGValidator(cfg).validate()
    assert exc_info.value.context["node_name"] == "orphan"


def test_static_loop_raises_correct_exception() -> None:
    cfg = _minimal_config()
    cfg["nodes"] = [
        {"name": "a", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
        {"name": "b", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
    ]
    cfg["edges"] = {
        "entry_point": "a",
        "static_edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
    }
    with pytest.raises(StaticLoopException):
        DLGValidator(cfg).validate()


def test_validate_module_imports_independently() -> None:
    DLGValidator(_minimal_config()).validate_module_imports()


def test_validate_graph_structure_independently() -> None:
    DLGValidator(_minimal_config()).validate_graph_structure()
