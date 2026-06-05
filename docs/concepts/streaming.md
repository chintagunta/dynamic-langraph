# Streaming

## Stream Modes

| Mode | Emits |
|------|-------|
| `"updates"` | State delta per node (only changed keys) |
| `"values"` | Full state after each superstep |
| `"messages"` | Token events for LLM nodes |
| `"custom"` | Events written via `stream_writer` |
| `"debug"` | Internal debug events |

## Usage

```python
async for event in graph.astream(inputs, stream_mode="updates"):
    print(event)
```

## Custom Events

```python
from langgraph.types import StreamWriter

async def my_node(state, config, *, writer: StreamWriter):
    writer({"status": "processing"})
    return {"result": "done"}
```

## Restricting Output Keys

Use `output_keys` to restrict which channels appear in `"values"` mode stream output.
