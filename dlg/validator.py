from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
from collections import deque
from pathlib import Path
from typing import Any

import jsonschema

from dlg._config import GraphConfig, SecurityConfig
from dlg._schema import DLG_METASCHEMA
from dlg.exceptions import (
    GraphValidationError,
    MixedRoutingConflict,
    SendTargetError,
    StaticLoopException,
    SubgraphCompatibilityError,
    UnreachableNodeException,
)


class DLGValidator:
    def __init__(
        self,
        config: dict[str, Any] | GraphConfig,
        *,
        security: SecurityConfig | None = None,
    ) -> None:
        if isinstance(config, GraphConfig):
            self._graph_config = config
            self._raw: dict[str, Any] = config.model_dump(by_alias=True)
        else:
            self._raw = config
            self._graph_config: GraphConfig | None = None  # type: ignore[assignment]

        self._security = security

    def _parsed(self) -> GraphConfig:
        if self._graph_config is None:
            try:
                self._graph_config = GraphConfig.model_validate(self._raw)
            except Exception as exc:
                raise GraphValidationError(
                    f"Config model parse error: {exc}",
                    {"reason": str(exc)},
                ) from exc
        return self._graph_config

    @classmethod
    def from_file(cls, path: str | Path) -> DLGValidator:
        p = Path(path)
        with p.open() as f:
            data = json.load(f)
        return cls(data)

    def validate(self) -> None:
        self._check_json_schema()
        cfg = self._parsed()
        security = self._security or cfg.security
        if security:
            self._check_security_allowlist(cfg, security)
        self.validate_module_imports()
        self.validate_graph_structure()
        self._check_send_targets(cfg)

    def validate_module_imports(self) -> None:
        cfg = self._parsed()
        for node in cfg.nodes:
            if node.handler:
                self._check_module_exists(node.handler.module_path, node.name)
                self._check_callable_exists(
                    node.handler.module_path,
                    node.handler.function_name,
                    node.name,
                )
                self._check_handler_signature(
                    node.handler.module_path,
                    node.handler.function_name,
                    node.name,
                )
        self._check_state_module(cfg)

    def validate_graph_structure(self) -> None:
        cfg = self._parsed()
        node_names = {n.name for n in cfg.nodes}
        self._check_cycle(cfg, node_names)
        self._check_reachability(cfg, node_names)
        self._check_mixed_routing(cfg)

    # ---- internal checks ----

    def _check_json_schema(self) -> None:
        validator = jsonschema.Draft202012Validator(DLG_METASCHEMA)
        errors = list(validator.iter_errors(self._raw))
        if errors:
            first = errors[0]
            path = "$." + ".".join(str(p) for p in first.absolute_path) if first.absolute_path else "$"
            raise GraphValidationError(
                f"JSON schema validation failed: {first.message}",
                {"field": path, "reason": first.message},
            )

    def _check_security_allowlist(self, cfg: GraphConfig, security: SecurityConfig) -> None:
        if not security.allowed_module_prefixes:
            return
        prefixes = security.allowed_module_prefixes

        modules_to_check: list[str] = []
        modules_to_check.append(cfg.state_definition.module_path)
        for node in cfg.nodes:
            if node.handler:
                modules_to_check.append(node.handler.module_path)

        for mod in modules_to_check:
            if not any(mod.startswith(p) for p in prefixes):
                raise GraphValidationError(
                    f"Module '{mod}' not in allowed_module_prefixes",
                    {"field": "module_path", "reason": f"'{mod}' not allowed by security policy"},
                )

    def _check_module_exists(self, module_path: str, node_name: str) -> None:
        try:
            spec = importlib.util.find_spec(module_path)
        except (ModuleNotFoundError, ValueError):
            spec = None
        if spec is None:
            raise GraphValidationError(
                f"Module '{module_path}' not found",
                {"field": f"nodes[{node_name}].handler.module_path", "reason": f"Module '{module_path}' not importable"},
            )

    def _check_callable_exists(self, module_path: str, function_name: str, node_name: str) -> None:
        try:
            mod = importlib.import_module(module_path)
        except ImportError as exc:
            raise GraphValidationError(
                f"Cannot import '{module_path}': {exc}",
                {"field": f"nodes[{node_name}].handler.module_path", "reason": str(exc)},
            ) from exc

        fn = getattr(mod, function_name, None)
        if fn is None or not callable(fn):
            raise GraphValidationError(
                f"'{function_name}' not found or not callable in '{module_path}'",
                {"field": f"nodes[{node_name}].handler.function_name", "reason": "not callable"},
            )

    def _check_handler_signature(self, module_path: str, function_name: str, node_name: str) -> None:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, function_name)
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        if len(params) == 0 or params[0] not in ("state",) and len(params) < 1:
            raise GraphValidationError(
                f"Handler '{function_name}' must accept at least a 'state' parameter",
                {"field": f"nodes[{node_name}].handler.function_name", "reason": "invalid signature"},
            )
        if len(params) > 3:
            raise GraphValidationError(
                f"Handler '{function_name}' has too many parameters (max 3: state, config/runtime, ...)",
                {"field": f"nodes[{node_name}].handler.function_name", "reason": "too many parameters"},
            )

    def _check_state_module(self, cfg: GraphConfig) -> None:
        sd = cfg.state_definition
        self._check_module_exists(sd.module_path, "state_definition")
        mod = importlib.import_module(sd.module_path)
        if not hasattr(mod, sd.class_name):
            raise GraphValidationError(
                f"State class '{sd.class_name}' not found in '{sd.module_path}'",
                {"field": "state_definition.class_name", "reason": "class not found"},
            )

    def _check_cycle(self, cfg: GraphConfig, node_names: set[str]) -> None:
        adj: dict[str, list[str]] = {n: [] for n in node_names}
        for edge in cfg.edges.static_edges:
            src = edge.from_node
            dst = edge.to_node
            if src in adj and dst in adj:
                adj[src].append(dst)

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> list[str] | None:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor, path + [neighbor])
                    if result is not None:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    return path[cycle_start:] + [neighbor]
            rec_stack.discard(node)
            return None

        for node in node_names:
            if node not in visited:
                cycle = dfs(node, [node])
                if cycle:
                    raise StaticLoopException(
                        f"Static loop detected: {cycle}",
                        {"cycle_nodes": cycle},
                    )

    def _check_reachability(self, cfg: GraphConfig, node_names: set[str]) -> None:
        # Send API creates runtime-dynamic dispatch; skip reachability when any node uses send_api
        if any(n.send_api for n in cfg.nodes):
            return

        reachable: set[str] = set()
        queue: deque[str] = deque([cfg.edges.entry_point])

        all_edges: dict[str, list[str]] = {n: [] for n in node_names}
        for edge in cfg.edges.static_edges:
            if edge.from_node in all_edges and edge.to_node in all_edges:
                all_edges[edge.from_node].append(edge.to_node)
        for cedge in cfg.edges.conditional_edges:
            if cedge.from_node in all_edges:
                if cedge.path_map:
                    for target in cedge.path_map.values():
                        if target in all_edges:
                            all_edges[cedge.from_node].append(target)

        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            for neighbor in all_edges.get(current, []):
                if neighbor not in reachable:
                    queue.append(neighbor)

        unreachable = node_names - reachable
        for node in sorted(unreachable):
            raise UnreachableNodeException(
                f"Node '{node}' is unreachable from entry point '{cfg.edges.entry_point}'",
                {"node_name": node},
            )

    def _check_mixed_routing(self, cfg: GraphConfig) -> None:
        static_sources = {e.from_node for e in cfg.edges.static_edges}
        conditional_sources = {e.from_node for e in cfg.edges.conditional_edges}
        conflicts = static_sources & conditional_sources
        for node in sorted(conflicts):
            raise MixedRoutingConflict(
                f"Node '{node}' has both static and conditional edges",
                {"node_name": node, "edge_types": ["static", "conditional"]},
            )

    def _check_send_targets(self, cfg: GraphConfig) -> None:
        node_names = {n.name for n in cfg.nodes}
        for cedge in cfg.edges.conditional_edges:
            if cedge.send_router is None:
                continue
            try:
                mod = importlib.import_module(cedge.send_router.module_path)
                fn = getattr(mod, cedge.send_router.function_name, None)
                if fn is None:
                    continue
                hints = getattr(fn, "__annotations__", {})
                ret = hints.get("return", None)
                if ret is not None:
                    ret_str = str(ret)
                    if "Send" not in ret_str and "list" not in ret_str.lower():
                        raise SendTargetError(
                            f"Send router '{cedge.send_router.function_name}' must return list[Send]",
                            {"router_node": cedge.from_node, "target_node": ""},
                        )
            except (ImportError, AttributeError):
                pass
