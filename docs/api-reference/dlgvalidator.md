# DLGValidator API Reference

## Constructor

```python
DLGValidator(config: dict | GraphConfig, *, security: SecurityConfig | None = None)
```

## Methods

| Method | Description |
|--------|-------------|
| `validate() -> None` | Runs all 11 validation checks. Raises on first failure. |
| `validate_module_imports() -> None` | Runs only module/callable/signature checks. |
| `validate_graph_structure() -> None` | Runs only structural checks (cycles, reachability, mixed routing). |
| `from_file(path) -> DLGValidator` | Classmethod — loads JSON config file. |

## Exceptions

| Exception | Trigger |
|-----------|---------|
| `GraphValidationError` | Schema, bad module, signature, allowlist |
| `StaticLoopException` | Deterministic cycle in static edges |
| `UnreachableNodeException` | Node not reachable from entry_point |
| `MixedRoutingConflict` | Same node in both static and conditional edges |
| `SendTargetError` | Send router targets undeclared node |
| `SubgraphCompatibilityError` | Subgraph state incompatible with parent |

## Example

```python
from dlg import DLGValidator

DLGValidator(config).validate()
```
