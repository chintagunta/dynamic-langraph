from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dlg.exceptions import (
    GraphValidationError,
    MixedRoutingConflict,
    StaticLoopException,
    UnreachableNodeException,
)
from dlg.validator import DLGValidator


def _base_config(**overrides: object) -> dict:
    cfg: dict = {
        "graph_id": "test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "nodes": [
            {
                "name": "node_a",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            }
        ],
        "edges": {
            "entry_point": "node_a",
            "static_edges": [{"from": "node_a", "to": "__end__"}],
        },
    }
    cfg.update(overrides)
    return cfg


def test_valid_config_passes() -> None:
    DLGValidator(_base_config()).validate()


def test_invalid_version_raises() -> None:
    cfg = _base_config(version="not-semver")
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate()


def test_missing_graph_id_raises() -> None:
    cfg = _base_config()
    del cfg["graph_id"]
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate()


def test_empty_nodes_raises() -> None:
    cfg = _base_config(nodes=[])
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate()


def test_security_allowlist_blocks_bad_module() -> None:
    cfg = _base_config(
        security={"allowed_module_prefixes": ["myapp"]},
    )
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate()


def test_security_allowlist_allows_matching_module() -> None:
    cfg = _base_config(
        security={"allowed_module_prefixes": ["tests"]},
    )
    DLGValidator(cfg).validate()


def test_nonexistent_module_raises() -> None:
    cfg = _base_config(
        nodes=[
            {
                "name": "node_a",
                "handler": {
                    "module_path": "nonexistent.module.xyz",
                    "function_name": "fn",
                },
            }
        ],
    )
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate_module_imports()


def test_nonexistent_function_raises() -> None:
    cfg = _base_config(
        nodes=[
            {
                "name": "node_a",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "nonexistent_fn",
                },
            }
        ],
    )
    with pytest.raises(GraphValidationError):
        DLGValidator(cfg).validate_module_imports()


def test_cycle_detection_raises_static_loop() -> None:
    cfg = _base_config(
        nodes=[
            {"name": "a", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
            {"name": "b", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
        ],
        edges={
            "entry_point": "a",
            "static_edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
        },
    )
    with pytest.raises(StaticLoopException) as exc_info:
        DLGValidator(cfg).validate_graph_structure()
    assert "cycle_nodes" in exc_info.value.context


def test_unreachable_node_raises() -> None:
    cfg = _base_config(
        nodes=[
            {"name": "a", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
            {"name": "orphan", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
        ],
        edges={
            "entry_point": "a",
            "static_edges": [{"from": "a", "to": "__end__"}],
        },
    )
    with pytest.raises(UnreachableNodeException) as exc_info:
        DLGValidator(cfg).validate_graph_structure()
    assert exc_info.value.context["node_name"] == "orphan"


def test_mixed_routing_conflict_raises() -> None:
    cfg = _base_config(
        nodes=[
            {"name": "a", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
            {"name": "b", "handler": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"}},
        ],
        edges={
            "entry_point": "a",
            "static_edges": [{"from": "a", "to": "b"}],
            "conditional_edges": [
                {
                    "from": "a",
                    "router": {"module_path": "tests.helpers.simple_nodes", "function_name": "echo_node"},
                    "path_map": {"x": "b"},
                }
            ],
        },
    )
    with pytest.raises(MixedRoutingConflict) as exc_info:
        DLGValidator(cfg).validate_graph_structure()
    assert exc_info.value.context["node_name"] == "a"


def test_validate_graph_structure_does_not_import() -> None:
    cfg = _base_config(
        nodes=[
            {
                "name": "node_a",
                "handler": {
                    "module_path": "totally.fake.module",
                    "function_name": "fn",
                },
            }
        ],
    )
    DLGValidator(cfg).validate_graph_structure()


def test_from_file_loads_config(tmp_path: object) -> None:
    import json
    import pathlib

    p = pathlib.Path(str(tmp_path)) / "cfg.json"
    p.write_text(json.dumps(_base_config()))
    v = DLGValidator.from_file(str(p))
    v.validate()
