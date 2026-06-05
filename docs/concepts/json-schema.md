# JSON Config Reference

## Minimal Valid Config

```json
{
  "graph_id": "hello_world",
  "version": "1.0.0",
  "state_definition": {
    "type": "typed_dict",
    "module_path": "my_app.state",
    "class_name": "SimpleState"
  },
  "nodes": [
    {
      "name": "echo",
      "handler": {
        "module_path": "my_app.nodes",
        "function_name": "echo_node"
      }
    }
  ],
  "edges": {
    "entry_point": "echo",
    "static_edges": [{ "from": "echo", "to": "__end__" }]
  }
}
```

## Reserved Node Names

- `__start__` — implicit graph entry
- `__end__` — implicit graph exit

## Version Field

Must match `^\d+\.\d+\.\d+$` (semantic versioning). Checked against checkpoint version at load.

## All Optional Fields

- `settings.recursion_limit` (default: 1000) — passed at runtime per invocation
- `settings.max_concurrency` — max parallel nodes per superstep
- `checkpointer` — persistence backend (`"memory"`, `"sqlite"`, `"custom"`)
- `cache` — graph-level cache (`"memory"`, `"custom"`)
- `security.allowed_module_prefixes` — module import allowlist
- `global_defaults.retry_policy` — default retry for all nodes
- Node: `retry_policy`, `timeout_seconds`, `interrupt_before`, `interrupt_after`, `cache_policy`, `fallback_node`, `send_api`
