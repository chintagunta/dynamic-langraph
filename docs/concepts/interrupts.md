# Interrupts (Human-in-the-Loop)

## interrupt_before / interrupt_after

```json
{
  "nodes": [{"name": "review", "handler": {...}, "interrupt_before": true}],
  "checkpointer": {"type": "memory"}
}
```

**Requires a checkpointer.** Raises `CheckpointerMissingError` if absent.

## Resume Pattern

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "t1"}}

# First invocation — pauses before "review" node
await graph.ainvoke(inputs, config=config)

# Resume with decision
result = await graph.ainvoke(Command(resume="approved"), config=config)
```

## interrupt() Inside Nodes

```python
from langgraph.types import interrupt

def review_node(state):
    decision = interrupt("Please approve or reject")
    return {"decision": decision}
```

## Multi-turn Conversation

For continuing without an interrupt, pass a plain dict (not `Command`) as subsequent input. Passing `Command` is only required after an `interrupt()` call.
