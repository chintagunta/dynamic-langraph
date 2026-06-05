# Subgraph Composition

```python
# my_app/subgraphs.py
from langgraph.graph import StateGraph
from my_app.state import SimpleState

def sub_node(state):
    return {"result": f"Sub: {state['message']}"}

g = StateGraph(SimpleState)
g.add_node("sub", sub_node)
g.set_entry_point("sub")
g.add_edge("sub", "__end__")
compiled_subgraph = g.compile()
```

Config using `subgraph` reference:

```json
{
  "nodes": [{
    "name": "sub_node",
    "subgraph": {"module_path": "my_app.subgraphs", "graph_name": "compiled_subgraph"}
  }]
}
```

```python
result = asyncio.run(graph.ainvoke({"message": "hello", "result": ""}))
assert result["result"] == "Sub: hello"
```
