# DLGCompiler / DLGEngine API Reference

## DLGEngine (recommended)

```python
DLGEngine(config: dict | GraphConfig)
```

| Method | Description |
|--------|-------------|
| `build() -> CompiledStateGraph` | Validates then compiles. |
| `from_file(path) -> CompiledStateGraph` | Classmethod — load + validate + compile. |

## DLGCompiler (low-level)

```python
DLGCompiler(config: dict | GraphConfig)
```

| Method | Description |
|--------|-------------|
| `compile() -> CompiledStateGraph` | Compiles without validation. |
| `get_interrupt_nodes() -> tuple[list[str], list[str]]` | Returns (interrupt_before, interrupt_after) node lists. |

## Compiled Graph Operations

```python
graph = DLGEngine.from_file("config.json")

# Invoke
result = await graph.ainvoke(inputs, config={"configurable": {"thread_id": "t1"}})

# Stream
async for event in graph.astream(inputs, stream_mode="updates"):
    print(event)

# Recursion limit (runtime, NOT compile-time)
result = await graph.ainvoke(inputs, config={"recursion_limit": 50, ...})

# Resume after interrupt
from langgraph.types import Command
result = await graph.ainvoke(Command(resume="approved"), config=config)
```

**Note**: `recursion_limit` is a runtime invocation parameter, not a compile-time setting.
