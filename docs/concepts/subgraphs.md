# Subgraph Composition

## Registration

```json
{
  "nodes": [{
    "name": "sub_node",
    "subgraph": {
      "module_path": "my_app.subgraphs",
      "graph_name": "compiled_subgraph"
    }
  }]
}
```

The `graph_name` attribute must be a `CompiledStateGraph` instance in the module.

## State Schema Compatibility

Subgraph state keys written back to parent must have a reducer defined in the parent state schema. Raises `SubgraphCompatibilityError` otherwise.

## Command(graph=Command.PARENT)

A subgraph node can route execution back to the parent graph:

```python
from langgraph.types import Command

def subgraph_node(state):
    return Command(graph=Command.PARENT, goto="parent_node")
```

## Checkpoint Namespacing

Each subgraph invocation gets its own namespace in the checkpointer, preventing state key collisions.
