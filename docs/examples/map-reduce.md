# Map-Reduce with Send API

```python
from langgraph.types import Send

def fan_out_passthrough(state):
    return {}

def fan_out_router(state):
    return [Send("process_item", {"items": [], "results": [], "_item": x}) for x in state["items"]]

def process_item(state):
    return {"results": [state["_item"].upper()]}
```

See [Send API concepts](../concepts/send-api.md) for the JSON config pattern.

```python
result = asyncio.run(graph.ainvoke({"items": ["a", "b", "c"], "results": []}))
assert sorted(result["results"]) == ["A", "B", "C"]
```
