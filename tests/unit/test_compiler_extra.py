from __future__ import annotations

import pytest

from dlg._config import GraphConfig
from dlg.compiler import DLGCompiler, DLGEngine
from dlg.exceptions import GraphValidationError


def _base_config(**overrides: object) -> dict:
    cfg: dict = {
        "graph_id": "extra_test",
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
    cfg.update(overrides)
    return cfg


def test_compiler_accepts_graph_config_instance() -> None:
    cfg = GraphConfig.model_validate(_base_config())
    compiler = DLGCompiler(cfg)
    graph = compiler.compile()
    assert graph is not None


def test_compiler_invalid_config_raises() -> None:
    with pytest.raises(GraphValidationError):
        DLGCompiler({"bad": "config"}).compile()


def test_compiler_with_global_defaults() -> None:
    cfg = _base_config(
        global_defaults={"retry_policy": {"max_attempts": 2, "initial_interval": 0.1, "backoff_factor": 1.5}}
    )
    compiler = DLGCompiler(cfg)
    graph = compiler.compile()
    assert graph is not None


async def test_compiler_interrupt_after_node() -> None:
    cfg = _base_config(
        checkpointer={"type": "memory"},
    )
    cfg["nodes"][0]["interrupt_after"] = True
    compiler = DLGCompiler(cfg)
    before, after = compiler.get_interrupt_nodes()
    assert "echo" in after
    graph = compiler.compile()
    assert graph is not None
