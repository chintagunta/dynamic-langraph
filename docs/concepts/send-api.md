# Send API (Map-Reduce)

## Pattern

1. A node processes state and returns a dict (or nothing)
2. A conditional edge uses a `send_router` that returns `list[Send]`
3. Each `Send` dispatches to a worker node with its own state slice
4. Worker node results aggregate via reducers

## Config

```json
{
  "nodes": [
    {"name": "fan_out", "handler": {"module_path": "...", "function_name": "passthrough"}, "send_api": true},
    {"name": "worker", "handler": {"module_path": "...", "function_name": "process"}}
  ],
  "edges": {
    "entry_point": "fan_out",
    "conditional_edges": [{
      "from": "fan_out",
      "send_router": {"module_path": "...", "function_name": "router_fn"}
    }],
    "static_edges": [{"from": "worker", "to": "__end__"}]
  }
}
```

## Router Function

```python
from langgraph.types import Send

def router_fn(state):
    return [Send("worker", {"item": x}) for x in state["items"]]
```

## Aggregation

Use `Annotated` reducer on state fields to collect parallel results:

```python
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    results: Annotated[list[str], lambda a, b: a + b]
```
