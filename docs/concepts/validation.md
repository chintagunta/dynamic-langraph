# Validation Reference

`DLGValidator` runs 11 checks in order. First failure raises.

| # | Check | Exception |
|---|-------|-----------|
| 1 | JSON Schema conformance | `GraphValidationError` |
| 2 | Security allowlist | `GraphValidationError` |
| 3 | Module existence | `GraphValidationError` |
| 4 | Callable attribute | `GraphValidationError` |
| 5 | Handler signature | `GraphValidationError` |
| 6 | Input/output schema subset | `GraphValidationError` |
| 7 | Cycle detection | `StaticLoopException` |
| 8 | Reachability analysis | `UnreachableNodeException` |
| 9 | Mixed routing conflict | `MixedRoutingConflict` |
| 10 | Send API target validation | `SendTargetError` |
| 11 | Subgraph compatibility | `SubgraphCompatibilityError` |

## Examples

**Bad version** → `GraphValidationError`:
```json
{ "version": "not-semver" }
```

**Cycle** → `StaticLoopException`:
```json
{ "static_edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}] }
```

**Unreachable node** → `UnreachableNodeException`:
```json
{ "nodes": ["a", "orphan"], "edges": {"entry_point": "a", "static_edges": [{"from": "a", "to": "__end__"}]} }
```
