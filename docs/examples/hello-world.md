# Hello World

Complete working example.

## State

```python
# my_app/state.py
from typing_extensions import TypedDict

class SimpleState(TypedDict):
    message: str
    result: str
```

## Node

```python
# my_app/nodes.py
def echo_node(state):
    return {"result": f"Echo: {state['message']}"}
```

## Config (`hello_world.json`)

```json
{
  "graph_id": "hello_world",
  "version": "1.0.0",
  "state_definition": {
    "type": "typed_dict",
    "module_path": "my_app.state",
    "class_name": "SimpleState"
  },
  "nodes": [{"name": "echo", "handler": {"module_path": "my_app.nodes", "function_name": "echo_node"}}],
  "edges": {
    "entry_point": "echo",
    "static_edges": [{"from": "echo", "to": "__end__"}]
  }
}
```

## Run

```python
import asyncio
from dlg import DLGEngine

graph = DLGEngine.from_file("hello_world.json")
result = asyncio.run(graph.ainvoke({"message": "hello", "result": ""}))
assert result["result"] == "Echo: hello"
```
