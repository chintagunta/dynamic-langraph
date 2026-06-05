# DynamicLangGraph Engine

`dynamic-langgraph` converts JSON configuration documents into compiled, executable LangGraph graphs.

## Installation

```bash
pip install dynamic-langgraph
```

## Quickstart

```python
import asyncio
from dlg import DLGEngine

graph = DLGEngine.from_file("graph_config.json")
result = asyncio.run(graph.ainvoke({"message": "hello"}))
```

See [examples/hello-world.md](examples/hello-world.md) for a complete walkthrough.
