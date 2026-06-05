from __future__ import annotations

import pytest

from dlg.exceptions import (
    CheckpointerMissingError,
    DLGError,
    GraphValidationError,
    MixedRoutingConflict,
    NodeTimeoutException,
    SchemaVersionMismatch,
    SendTargetError,
    StaticLoopException,
    SubgraphCompatibilityError,
    UnreachableNodeException,
)


def test_dlg_error_base() -> None:
    err = DLGError("test message", {"key": "value"})
    assert err.message == "test message"
    assert err.context == {"key": "value"}
    assert str(err) == "test message"


def test_dlg_error_default_context() -> None:
    err = DLGError("msg")
    assert err.context == {}


def test_graph_validation_error_is_dlg_error() -> None:
    err = GraphValidationError("bad config", {"field": "nodes"})
    assert isinstance(err, DLGError)
    assert err.context["field"] == "nodes"


def test_static_loop_exception_hierarchy() -> None:
    err = StaticLoopException("loop", {"cycle_nodes": ["a", "b"]})
    assert isinstance(err, GraphValidationError)
    assert isinstance(err, DLGError)
    assert err.context["cycle_nodes"] == ["a", "b"]


def test_unreachable_node_exception() -> None:
    err = UnreachableNodeException("unreachable", {"node_name": "orphan"})
    assert isinstance(err, GraphValidationError)
    assert err.context["node_name"] == "orphan"


def test_mixed_routing_conflict() -> None:
    err = MixedRoutingConflict("conflict", {"node_name": "n", "edge_types": ["static", "conditional"]})
    assert isinstance(err, GraphValidationError)
    assert err.context["edge_types"] == ["static", "conditional"]


def test_send_target_error() -> None:
    err = SendTargetError("bad target", {"router_node": "r", "target_node": "x"})
    assert isinstance(err, GraphValidationError)


def test_subgraph_compatibility_error() -> None:
    err = SubgraphCompatibilityError("incompat", {"subgraph_node": "sub", "incompatible_keys": ["k"], "reason": "no reducer"})
    assert isinstance(err, GraphValidationError)


def test_node_timeout_exception() -> None:
    err = NodeTimeoutException("timeout", {"node_name": "n", "timeout_seconds": 5.0, "elapsed_seconds": 6.0})
    assert isinstance(err, DLGError)
    assert not isinstance(err, GraphValidationError)


def test_checkpointer_missing_error() -> None:
    err = CheckpointerMissingError("missing", {"operation": "interrupt"})
    assert isinstance(err, DLGError)
    assert err.context["operation"] == "interrupt"


def test_schema_version_mismatch() -> None:
    err = SchemaVersionMismatch("mismatch", {"config_version": "2.0.0", "checkpoint_version": "1.0.0", "thread_id": "t1"})
    assert isinstance(err, DLGError)
    assert err.context["config_version"] == "2.0.0"


def test_all_exceptions_instantiate_with_message_and_context() -> None:
    classes = [
        DLGError,
        GraphValidationError,
        StaticLoopException,
        UnreachableNodeException,
        MixedRoutingConflict,
        SendTargetError,
        SubgraphCompatibilityError,
        NodeTimeoutException,
        CheckpointerMissingError,
        SchemaVersionMismatch,
    ]
    for cls in classes:
        err = cls("msg", {"k": "v"})
        assert err.message == "msg"
        assert err.context == {"k": "v"}
