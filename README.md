# dynamic-langgraph — DynamicLangGraph Engine

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
- **Graph visualization** — export to Mermaid (`.mmd`) and images (PNG, SVG, JPG, PDF)
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
uv sync --dev
```

---

## Quickstart

### 1. Write a JSON config

```json
{
  "graph_id": "echo-graph",
  "version": "1.0.0",
  "state_definition": {
    "type": "typed_dict",
    "module_path": "myapp.state",
    "class_name": "EchoState"
  },
  "nodes": [
    {
      "name": "echo",
      "handler": {
        "module_path": "myapp.nodes",
        "function_name": "echo_node"
      }
    }
  ],
  "edges": {
    "entry_point": "echo",
    "static_edges": [
      {"from": "echo", "to": "__end__"}
    ]
  }
}
```

### 2. Compile and run

```python
import asyncio
from dlg import DLGEngine

graph = DLGEngine.from_file("graph_config.json")
result = asyncio.run(graph.ainvoke({"message": "hello"}))
print(result)
```

Or validate and compile separately:

```python
from dlg import DLGValidator, DLGCompiler

config = {"graph_id": "echo-graph", "version": "1.0.0", ...}

DLGValidator(config).validate()
graph = DLGCompiler(config).compile()
```

---

## Human-in-the-Loop

Add `"interrupt_before": true` to a node and provide a checkpointer:

```json
{
  "nodes": [
    {
      "name": "review",
      "handler": {"module_path": "myapp.nodes", "function_name": "review_node"},
      "interrupt_before": true
    }
  ],
  "checkpointer": {"type": "memory"}
}
```

```python
import asyncio
from langgraph.types import Command
from dlg import DLGEngine

graph = DLGEngine.from_file("graph_config.json")
thread = {"configurable": {"thread_id": "session-1"}}

# Pauses at the interrupt_before node
await graph.ainvoke({"task": "review this"}, config=thread)

# Resume after human decision
result = await graph.ainvoke(Command(resume="approved"), config=thread)
```

---

## Map-Reduce Fan-Out

```json
{
  "edges": {
    "entry_point": "fan_out",
    "conditional_edges": [
      {
        "from": "fan_out",
        "send_router": {
          "module_path": "myapp.routers",
          "function_name": "fan_out_router"
        }
      }
    ]
  }
}
```

```python
from langgraph.types import Send

def fan_out_router(state):
    return [Send("process_item", {"item": x}) for x in state["items"]]
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

### Python API

```python
from dlg.mermaid import json_to_mermaid, convert_json_to_mmd, convert_mmd_to_image

# Get Mermaid diagram text from a config dict
config = {"graph_id": "my-graph", "version": "1.0.0", ...}
print(json_to_mermaid(config))
# flowchart TD
#     __start__((__start__)) --> echo
#     echo --> __end__((__end__))

# Write .mmd beside the JSON file
mmd_path = convert_json_to_mmd("graph_config.json")
# -> graph_config.mmd

# Convert .mmd to PNG (requires mmdc or npx)
img_path = convert_mmd_to_image(mmd_path, "png")
# -> graph_config.png

# Write image to a specific output directory
img_path = convert_mmd_to_image(mmd_path, "png", output_dir="graph-previews/")
# -> graph-previews/graph_config.png
```

### CLI

```bash
# Generate .mmd only
python -m dlg graph_config.json

# Generate .mmd and a PNG
python -m dlg graph_config.json --format png

# Generate .mmd, PNG and SVG into a target folder
python -m dlg graph_config.json -f png -f svg --output-dir graph-previews/

# After pip install dynamic-langgraph:
dlg graph_config.json -f png --output-dir graph-previews/
```

`mmdc` from [`@mermaid-js/mermaid-cli`](https://github.com/mermaid-js/mermaid-cli) is required for image export.
Install globally with `npm i -g @mermaid-js/mermaid-cli`, or ensure `npx` is available (falls back automatically).

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

harness = DLGTestHarness(config)
result = await harness.invoke_node("echo", state={"message": "hi"})
assert result["message"] == "hi"
```

---

## Configuration Reference

A full JSON config supports the following top-level keys:

| Key | Required | Description |
|---|---|---|
| `graph_id` | Yes | Unique graph identifier |
| `version` | Yes | Semantic version string (e.g. `"1.0.0"`) |
| `state_definition` | Yes | State schema — `type` (`typed_dict`, `pydantic`, `dataclass`), `module_path`, `class_name` |
| `nodes` | Yes | List of node descriptors (each with `name` and `handler` or `subgraph`) |
| `edges` | Yes | `entry_point`, `static_edges`, `conditional_edges` |
| `checkpointer` | No | `{"type": "memory"}`, `{"type": "sqlite", "db_path": "..."}`, or custom |
| `settings` | No | `recursion_limit`, `max_concurrency` |
| `global_defaults` | No | Default `retry_policy`, `timeout_seconds` |
| `cache` | No | Global cache policy |
| `security` | No | `allowed_module_prefixes` allowlist |

See [docs/concepts/json-schema.md](docs/concepts/json-schema.md) for the full schema reference.

---

## Project Structure

```
dlg/
├── __init__.py        # Public API exports
├── __main__.py        # CLI entry point (python -m dlg / dlg command)
├── compiler.py        # DLGCompiler — StateGraph assembly
├── mermaid.py         # Mermaid/image export (json_to_mermaid, convert_*)
├── validator.py       # DLGValidator — all pre-compilation checks
├── exceptions.py      # Typed exception hierarchy
├── testing.py         # DLGTestHarness utility
├── _config.py         # Pydantic config models (GraphConfig, NodeConfig, …)
├── _schema.py         # JSON metaschema
├── _wrappers.py       # Async node wrapper + sync adapter
└── _telemetry.py      # LangSmith integration

tests/
├── unit/              # DLGValidator, DLGCompiler, mermaid, models
└── integration/       # Full graph execution, streaming, checkpointing

docs/                  # MkDocs site (concepts, API reference, examples)
```

---

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run python -m pytest

# Run tests with coverage
uv run python -m pytest --cov=dlg --cov-report=term-missing

# Type check
uv run mypy dlg --strict

# Build docs locally
uv run mkdocs serve
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
