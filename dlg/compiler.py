from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from dlg._config import GraphConfig
from dlg._wrappers import create_async_wrapper
from dlg.exceptions import CheckpointerMissingError, GraphValidationError


class DLGCompiler:
    def __init__(self, config: dict[str, Any] | GraphConfig) -> None:
        if isinstance(config, GraphConfig):
            self._config = config
        else:
            try:
                self._config = GraphConfig.model_validate(config)
            except Exception as exc:
                raise GraphValidationError(f"Config parse error: {exc}", {"reason": str(exc)}) from exc

    def get_interrupt_nodes(self) -> tuple[list[str], list[str]]:
        before = [n.name for n in self._config.nodes if n.interrupt_before]
        after = [n.name for n in self._config.nodes if n.interrupt_after]
        return before, after

    def compile(self) -> CompiledStateGraph:
        cfg = self._config
        state_class = self._resolve_state(cfg)
        checkpointer = self._resolve_checkpointer(cfg)

        interrupt_before, interrupt_after = self.get_interrupt_nodes()
        if (interrupt_before or interrupt_after) and checkpointer is None:
            raise CheckpointerMissingError(
                "Interrupt nodes require a checkpointer",
                {"operation": "interrupt"},
            )

        graph = StateGraph(state_class)

        for node in cfg.nodes:
            if node.subgraph:
                compiled_subgraph = self._resolve_subgraph(node.subgraph)
                graph.add_node(node.name, compiled_subgraph)
            elif node.handler:
                mod = importlib.import_module(node.handler.module_path)
                fn = getattr(mod, node.handler.function_name)
                wrapped = create_async_wrapper(node, fn)
                graph.add_node(node.name, wrapped)

        for edge in cfg.edges.static_edges:
            graph.add_edge(edge.from_node, edge.to_node)

        for cedge in cfg.edges.conditional_edges:
            if cedge.send_router:
                mod = importlib.import_module(cedge.send_router.module_path)
                router_fn = getattr(mod, cedge.send_router.function_name)
                graph.add_conditional_edges(cedge.from_node, router_fn)
            elif cedge.router and cedge.path_map:
                mod = importlib.import_module(cedge.router.module_path)
                router_fn = getattr(mod, cedge.router.function_name)
                graph.add_conditional_edges(cedge.from_node, router_fn, cedge.path_map)

        graph.set_entry_point(cfg.edges.entry_point)

        compile_kwargs: dict[str, Any] = {}
        if checkpointer is not None:
            compile_kwargs["checkpointer"] = checkpointer
        if interrupt_before:
            compile_kwargs["interrupt_before"] = interrupt_before
        if interrupt_after:
            compile_kwargs["interrupt_after"] = interrupt_after

        return graph.compile(**compile_kwargs)

    def _resolve_state(self, cfg: GraphConfig) -> Any:
        sd = cfg.state_definition
        mod = importlib.import_module(sd.module_path)
        state_class = getattr(mod, sd.class_name)
        return state_class

    def _resolve_checkpointer(self, cfg: GraphConfig) -> Any:
        if cfg.checkpointer is None:
            return None
        cp = cfg.checkpointer
        if cp.type == "memory":
            return InMemorySaver()
        if cp.type == "sqlite":
            from langgraph.checkpoint.sqlite import SqliteSaver
            db_path = cp.db_path or ":memory:"
            return SqliteSaver.from_conn_string(db_path)
        if cp.type == "custom":
            if cp.module_path is None or cp.class_name is None:
                raise GraphValidationError(
                    "Custom checkpointer requires module_path and class_name",
                    {"field": "checkpointer"},
                )
            mod = importlib.import_module(cp.module_path)
            cls = getattr(mod, cp.class_name)
            return cls()
        return None

    def _resolve_subgraph(self, subgraph_ref: Any) -> Any:
        mod = importlib.import_module(subgraph_ref.module_path)
        return getattr(mod, subgraph_ref.graph_name)


class DLGEngine:
    def __init__(self, config: dict[str, Any] | GraphConfig) -> None:
        self._config = config

    def build(self) -> CompiledStateGraph:
        from dlg.validator import DLGValidator

        DLGValidator(self._config).validate()
        return DLGCompiler(self._config).compile()

    @classmethod
    def from_file(cls, path: str | Path) -> CompiledStateGraph:
        p = Path(path)
        with p.open() as f:
            data = json.load(f)
        return cls(data).build()
