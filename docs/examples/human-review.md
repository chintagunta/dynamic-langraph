# Human Review (Interrupt/Resume)

```python
# my_app/nodes.py
from langgraph.types import interrupt

def human_review_node(state):
    decision = interrupt("Approve this result?")
    return {"result": f"Decision: {decision}"}
```

Config with `interrupt_before: true` and `checkpointer: {type: memory}`.

```python
import asyncio
from langgraph.types import Command
from dlg import DLGEngine

async def run():
    graph = DLGEngine.from_file("human_review.json")
    config = {"configurable": {"thread_id": "t1"}}

    await graph.ainvoke({"message": "hello", "result": ""}, config=config)
    result = await graph.ainvoke(Command(resume="approved"), config=config)
    assert result["result"] == "Decision: approved"

asyncio.run(run())
```
