from __future__ import annotations

import pytest
from pydantic import ValidationError

from dlg._config import (
    CachePolicyConfig,
    CheckpointerConfig,
    ConditionalEdge,
    EdgeConfig,
    FieldSpec,
    GlobalDefaultsConfig,
    GraphConfig,
    HandlerRef,
    NodeConfig,
    RetryPolicyConfig,
    SchemaRef,
    SecurityConfig,
    SettingsConfig,
    StateDefinitionConfig,
    StaticEdge,
    SubgraphRef,
    TelemetryConfig,
)


def _minimal_graph_config() -> dict:
    return {
        "graph_id": "test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "my.module",
            "class_name": "MyState",
        },
        "nodes": [{"name": "n", "handler": {"module_path": "my.module", "function_name": "fn"}}],
        "edges": {"entry_point": "n"},
    }


def test_graph_config_parses_minimal() -> None:
    cfg = GraphConfig.model_validate(_minimal_graph_config())
    assert cfg.graph_id == "test"
    assert cfg.version == "1.0.0"
    assert len(cfg.nodes) == 1


def test_graph_config_defaults() -> None:
    cfg = GraphConfig.model_validate(_minimal_graph_config())
    assert cfg.settings.recursion_limit == 1000
    assert cfg.checkpointer is None
    assert cfg.cache is None
    assert cfg.security is None


def test_node_config_requires_handler_or_subgraph() -> None:
    with pytest.raises(ValidationError):
        NodeConfig.model_validate({"name": "n"})


def test_node_config_rejects_both() -> None:
    with pytest.raises(ValidationError):
        NodeConfig.model_validate({
            "name": "n",
            "handler": {"module_path": "m", "function_name": "f"},
            "subgraph": {"module_path": "m", "graph_name": "g"},
        })


def test_static_edge_parses_from_to() -> None:
    e = StaticEdge.model_validate({"from": "a", "to": "b"})
    assert e.from_node == "a"
    assert e.to_node == "b"


def test_retry_policy_defaults() -> None:
    rp = RetryPolicyConfig()
    assert rp.max_attempts == 3
    assert rp.initial_interval == 1.0
    assert rp.backoff_factor == 2.0
    assert rp.retryable_exceptions == []


def test_checkpointer_config_types() -> None:
    c = CheckpointerConfig.model_validate({"type": "memory"})
    assert c.type == "memory"


def test_settings_config_defaults() -> None:
    s = SettingsConfig()
    assert s.recursion_limit == 1000
    assert s.max_concurrency is None


def test_state_definition_typed_dict() -> None:
    sd = StateDefinitionConfig.model_validate({
        "type": "typed_dict",
        "module_path": "m",
        "class_name": "C",
    })
    assert sd.type == "typed_dict"
    assert not sd.use_messages_preset


def test_field_spec_parses() -> None:
    fs = FieldSpec.model_validate({"type": "str", "reducer": "operator.add"})
    assert fs.type == "str"
    assert fs.reducer == "operator.add"


def test_security_config_empty_prefixes() -> None:
    sec = SecurityConfig()
    assert sec.allowed_module_prefixes == []


def test_handler_ref_parses() -> None:
    h = HandlerRef.model_validate({"module_path": "m", "function_name": "f"})
    assert h.module_path == "m"
    assert h.function_name == "f"
