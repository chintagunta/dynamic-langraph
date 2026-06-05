# Persistence

## Checkpointer Types

| Type | Config | Notes |
|------|--------|-------|
| `"memory"` | `{"type": "memory"}` | In-process; lost on restart |
| `"sqlite"` | `{"type": "sqlite", "db_path": "graph.db"}` | On-disk persistence |
| `"custom"` | `{"type": "custom", "module_path": "...", "class_name": "..."}` | Bring your own |

## Thread Identity

Every invocation with a checkpointer requires a `thread_id`:

```python
config = {"configurable": {"thread_id": "user-123"}}
result = await graph.ainvoke(inputs, config=config)
```

## State Inspection

```python
snapshot = graph.get_state(config)
history = list(graph.get_state_history(config))
```

## SchemaVersionMismatch

If `config.version` differs from the stored checkpoint version, `SchemaVersionMismatch` is raised with `context={"config_version": ..., "checkpoint_version": ..., "thread_id": ...}`.
