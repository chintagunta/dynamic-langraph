from __future__ import annotations

DLG_METASCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["graph_id", "version", "state_definition", "nodes", "edges"],
    "additionalProperties": True,
    "properties": {
        "graph_id": {"type": "string", "minLength": 1},
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+\.\d+$",
        },
        "state_definition": {
            "type": "object",
            "required": ["type", "module_path", "class_name"],
            "properties": {
                "type": {"type": "string", "enum": ["pydantic", "typed_dict", "dataclass"]},
                "module_path": {"type": "string", "minLength": 1},
                "class_name": {"type": "string", "minLength": 1},
            },
        },
        "nodes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "handler": {
                        "type": "object",
                        "required": ["module_path", "function_name"],
                        "properties": {
                            "module_path": {"type": "string"},
                            "function_name": {"type": "string"},
                        },
                    },
                    "subgraph": {
                        "type": "object",
                        "required": ["module_path", "graph_name"],
                        "properties": {
                            "module_path": {"type": "string"},
                            "graph_name": {"type": "string"},
                        },
                    },
                },
            },
        },
        "edges": {
            "type": "object",
            "required": ["entry_point"],
            "properties": {
                "entry_point": {"type": "string", "minLength": 1},
                "static_edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["from", "to"],
                        "properties": {
                            "from": {"type": "string"},
                            "to": {"type": "string"},
                        },
                    },
                },
                "conditional_edges": {
                    "type": "array",
                    "items": {"type": "object", "required": ["from"]},
                },
            },
        },
    },
}

# Reserved node names — cannot be used as user-defined node names
RESERVED_NODE_NAMES = {"__start__", "__end__"}
