from __future__ import annotations

import json
from pathlib import Path

import pytest

from dlg.validator import DLGValidator

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples_py"

EXAMPLE_JSONS = sorted(EXAMPLES_DIR.rglob("*.json"))


@pytest.mark.parametrize("json_path", EXAMPLE_JSONS, ids=lambda p: p.stem)
def test_example_json_schema_valid(json_path: Path) -> None:
    validator = DLGValidator.from_file(json_path)
    validator._check_json_schema()


@pytest.mark.parametrize("json_path", EXAMPLE_JSONS, ids=lambda p: p.stem)
def test_example_graph_structure_valid(json_path: Path) -> None:
    validator = DLGValidator.from_file(json_path)
    validator._check_json_schema()
    validator.validate_graph_structure()


@pytest.mark.parametrize("json_path", EXAMPLE_JSONS, ids=lambda p: p.stem)
def test_example_json_has_required_fields(json_path: Path) -> None:
    data = json.loads(json_path.read_text())
    assert "graph_id" in data
    assert "version" in data
    assert "state_definition" in data
    assert "nodes" in data
    assert len(data["nodes"]) >= 1
    assert "edges" in data
    assert "entry_point" in data["edges"]


@pytest.mark.parametrize("json_path", EXAMPLE_JSONS, ids=lambda p: p.stem)
def test_example_entry_point_is_defined_node(json_path: Path) -> None:
    data = json.loads(json_path.read_text())
    node_names = {n["name"] for n in data["nodes"]}
    assert data["edges"]["entry_point"] in node_names
