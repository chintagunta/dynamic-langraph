# dynamic-langgraph — DynamicLangGraph Engine

[![CI](https://github.com/your-org/dynamic-langgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/dynamic-langgraph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dynamic-langgraph)](https://pypi.org/project/dynamic-langgraph/)
[![Python versions](https://img.shields.io/pypi/pyversions/dynamic-langgraph)](https://pypi.org/project/dynamic-langgraph/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)]()

**Build LangGraph graphs from JSON configuration — no hardcoded topologies.**

`dynamic-langgraph` is a Python library that converts declarative JSON config documents into fully compiled, executable [LangGraph](https://github.com/langchain-ai/langgraph) graphs. Define your nodes, edges, state schema, and execution settings in JSON. The engine validates, compiles, and hands you back an async-ready graph.

---

## Features

- **JSON-driven graph construction** — declare nodes, edges, and state in config; skip the boilerplate
- **Pre-compilation validation** — catches unreachable nodes, static cycles, bad module paths, and signature mismatches before any node runs
- **Async-first** — sync handlers are auto-wrapped in `run_in_executor`; no event loop blocking
- **Human-in-the-loop** — `interrupt_before`/`interrupt_after` breakpoints with `Command(resume=...)` support
- **Map-reduce fan-out** — `Send` API for parallel branch execution and aggregation
- **Nested subgraphs** — register compiled `CompiledStateGraph` instances as nodes in a parent graph
- **Streaming** — all 5 LangGraph stream modes (`values`, `updates`, `debug`, `messages`, `custom`)
- **Persistence** — `InMemorySaver`, `SqliteSaver`, or any custom `BaseCheckpointSaver`
- **Per-node caching** — `CachePolicy` with configurable TTL
- **LangSmith telemetry** — structured trace attributes emitted automatically
- **Graph visualization** — ASCII and Mermaid/PNG output with no extra code
- **Strictly typed** — fully annotated public API; passes `mypy --strict`

---

## Requirements

- Python 3.11+
- `langgraph >= 1.0.6`
- `jsonschema >= 4.23`

---

## Installation

```bash
pip install dynamic-langgraph
```

**From source (development):**

```bash
git clone https://github.com/your-org/dynamic-langgraph.git
cd dynamic-langgraph
uv pip install -e ".[dev]"
```

---

## Quickstart

### 1. Write a JSON config

```json
{
  "graph_id": "echo-graph",
  "version": "1.0.0",
  "state_definition": {
    "type": "TypedDict",
    "fields": {
      "message": "str",
      "result": "str"
    }
  },
  "nodes": [
    {
      "id": "echo",
      "module_path": "myapp.handlers",
      "callable": "echo_handler"
    }
  ],
  "edges": [
    { "from": "__start__", "to": "echo" },
    { "from": "echo", "to": "__end__" }
  ]
}
```

### 2. Compile and run

```python
import asyncio
from dlg import DLGValidator, DLGCompiler

config = open("graph_config.json").read()

validator = DLGValidator()
validator.validate(config)

compiler = DLGCompiler()
graph = compiler.compile(config)

result = asyncio.run(graph.ainvoke({"message": "hello", "result": ""}))
print(result["result"])  # Echo: hello
```

---

## Human-in-the-Loop

```python
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver

graph = compiler.compile(config, checkpointer=InMemorySaver())
thread = {"configurable": {"thread_id": "session-1"}}

# First call — pauses at the interrupt_before node
await graph.ainvoke({"task": "review this"}, config=thread)

# Resume after human decision
result = await graph.ainvoke(Command(resume="approved"), config=thread)
```

---

## Map-Reduce Fan-Out

```python
# Node flagged send_api: true returns a list of Send objects
from langgraph.types import Send

def fan_out_router(state):
    return [Send("process_item", {"item": x}) for x in state["items"]]
```

```json
{
  "id": "fan_out",
  "module_path": "myapp.routers",
  "callable": "fan_out_router",
  "send_api": true
}
```

---

## Streaming

```python
async for event in graph.astream(inputs, stream_mode="updates"):
    print(event)
```

Supported modes: `"values"`, `"updates"`, `"debug"`, `"messages"`, `"custom"`.

---

## Graph Visualization

```python
print(graph.get_graph().draw_ascii())
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

---

## Error Hierarchy

All validation errors are raised before any node executes.

| Exception | Trigger |
|---|---|
| `GraphValidationError` | Schema violation, missing field, bad module path |
| `UnreachableNodeException` | Node with no path from entry point |
| `StaticLoopException` | Cycle in static-only edges |
| `MixedRoutingConflict` | Node has both static edge and `Command(goto=...)` |
| `SendTargetError` | `Send` targets an undeclared node |
| `SubgraphCompatibilityError` | Subgraph state schema conflicts with parent |
| `CheckpointerMissingError` | Interrupt/resume attempted without checkpointer |
| `SchemaVersionMismatch` | Checkpoint config version differs from current config |

---

## Testing Utilities

```python
from dlg.testing import DLGTestHarness

harness = DLGTestHarness()
result = await harness.invoke_node("my_node", state={"x": 1}, config=config)
assert result["x"] == 2
```

---

## Configuration Reference

A full JSON config supports the following top-level keys:

| Key | Required | Description |
|---|---|---|
| `graph_id` | Yes | Unique graph identifier |
| `version` | Yes | Semantic version string (e.g. `"1.0.0"`) |
| `state_definition` | Yes | State schema (`TypedDict`, `Pydantic`, or `dataclass`) |
| `nodes` | Yes | List of node descriptors |
| `edges` | Yes | List of edge descriptors |
| `settings` | No | `recursion_limit`, `allowed_module_prefixes` |
| `global_defaults` | No | Default retry policy, timeout |
| `checkpointer` | No | `InMemorySaver`, `SqliteSaver`, or custom class |
| `cache` | No | Global cache policy |
| `context_schema` | No | Typed runtime context injected via `Runtime[...]` |

See [docs/concepts/json-schema.md](docs/concepts/json-schema.md) for the full schema reference.

---

## Project Structure

```
dlg/
├── __init__.py        # Public API exports
├── validator.py       # DLGValidator — all pre-compilation checks
├── compiler.py        # DLGCompiler — StateGraph assembly
├── exceptions.py      # Typed exception hierarchy
├── testing.py         # DLGTestHarness utility
├── _config.py         # Pydantic config models
├── _schema.py         # JSON metaschema
├── _wrappers.py       # Async node wrapper + sync adapter
└── _telemetry.py      # LangSmith integration

tests/
├── unit/              # DLGValidator, DLGCompiler, models
└── integration/       # Full graph execution, streaming, checkpointing

docs/                  # MkDocs site (concepts, API reference, examples)
```

---

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=dlg --cov-report=term-missing

# Type check
mypy dlg --strict

# Build docs locally
mkdocs serve
```

---

## Contributing

1. Fork the repo and create a feature branch
2. Add tests for new behavior (coverage target: 90%)
3. Ensure `mypy --strict` passes
4. Open a pull request — CI runs on Python 3.11, 3.12, and 3.13

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

## Acknowledgements

Built on top of [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain, Inc.
