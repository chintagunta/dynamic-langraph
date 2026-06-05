# Exceptions API Reference

## Hierarchy

```
Exception
└── DLGError
    ├── GraphValidationError
    │   ├── StaticLoopException
    │   ├── UnreachableNodeException
    │   ├── MixedRoutingConflict
    │   ├── SendTargetError
    │   └── SubgraphCompatibilityError
    ├── NodeTimeoutException
    ├── CheckpointerMissingError
    └── SchemaVersionMismatch
```

All exceptions carry `message: str` and `context: dict`.

## Context Keys

| Exception | context keys |
|-----------|-------------|
| `GraphValidationError` | `field`, `node`, `reason` |
| `StaticLoopException` | `cycle_nodes: list[str]` |
| `UnreachableNodeException` | `node_name: str` |
| `MixedRoutingConflict` | `node_name: str`, `edge_types: list[str]` |
| `SendTargetError` | `router_node: str`, `target_node: str` |
| `SubgraphCompatibilityError` | `subgraph_node: str`, `incompatible_keys: list[str]`, `reason: str` |
| `NodeTimeoutException` | `node_name: str`, `timeout_seconds: float`, `elapsed_seconds: float` |
| `CheckpointerMissingError` | `operation: str` |
| `SchemaVersionMismatch` | `config_version: str`, `checkpoint_version: str`, `thread_id: str` |

## Example

```python
from dlg import DLGValidator, UnreachableNodeException

try:
    DLGValidator(config).validate()
except UnreachableNodeException as e:
    print(f"Node '{e.context['node_name']}' is unreachable")
```
