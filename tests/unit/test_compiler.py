from __future__ import annotations

import pytest

from dlg._config import GraphConfig
from dlg.compiler import DLGCompiler, DLGEngine


def _minimal_config() -> dict:
    return {
        "graph_id": "test",
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


def test_compiler_compile_returns_compiled_graph() -> None:
    compiler = DLGCompiler(_minimal_config())
    graph = compiler.compile()
    assert graph is not None


def test_compiler_get_interrupt_nodes_empty() -> None:
    compiler = DLGCompiler(_minimal_config())
    before, after = compiler.get_interrupt_nodes()
    assert before == []
    assert after == []


def test_compiler_interrupt_nodes_extracted() -> None:
    cfg = _minimal_config()
    cfg["nodes"][0]["interrupt_before"] = True
    compiler = DLGCompiler(cfg)
    before, after = compiler.get_interrupt_nodes()
    assert "echo" in before
    assert after == []


def test_engine_build_returns_compiled_graph() -> None:
    engine = DLGEngine(_minimal_config())
    graph = engine.build()
    assert graph is not None


def test_engine_from_file(tmp_path: object) -> None:
    import json
    import pathlib

    p = pathlib.Path(str(tmp_path)) / "cfg.json"
    p.write_text(json.dumps(_minimal_config()))
    graph = DLGEngine.from_file(str(p))
    assert graph is not None


def test_compiler_with_memory_checkpointer() -> None:
    cfg = _minimal_config()
    cfg["checkpointer"] = {"type": "memory"}
    compiler = DLGCompiler(cfg)
    graph = compiler.compile()
    assert graph is not None


def test_compiler_with_async_handler() -> None:
    cfg = _minimal_config()
    cfg["nodes"][0]["handler"]["function_name"] = "async_echo_node"
    compiler = DLGCompiler(cfg)
    graph = compiler.compile()
    assert graph is not None
