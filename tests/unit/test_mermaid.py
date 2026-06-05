from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dlg.mermaid import convert_json_to_mmd, convert_mmd_to_image, json_to_mermaid


def _simple_config() -> dict:
    return {
        "graph_id": "test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "nodes": [
            {
                "name": "echo",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            }
        ],
        "edges": {
            "entry_point": "echo",
            "static_edges": [{"from": "echo", "to": "__end__"}],
        },
    }


def _conditional_config() -> dict:
    return {
        "graph_id": "cond_test",
        "version": "1.0.0",
        "state_definition": {
            "type": "typed_dict",
            "module_path": "tests.helpers.simple_state",
            "class_name": "SimpleState",
        },
        "nodes": [
            {
                "name": "gather",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            },
            {
                "name": "respond",
                "handler": {
                    "module_path": "tests.helpers.simple_nodes",
                    "function_name": "echo_node",
                },
            },
        ],
        "edges": {
            "entry_point": "gather",
            "static_edges": [{"from": "respond", "to": "__end__"}],
            "conditional_edges": [
                {
                    "from": "gather",
                    "router": {
                        "module_path": "tests.helpers.simple_nodes",
                        "function_name": "echo_node",
                    },
                    "path_map": {"gather": "gather", "respond": "respond"},
                }
            ],
        },
    }


# --- json_to_mermaid ---


def test_mermaid_starts_with_flowchart() -> None:
    out = json_to_mermaid(_simple_config())
    assert out.startswith("flowchart TD")


def test_mermaid_entry_point_edge() -> None:
    out = json_to_mermaid(_simple_config())
    assert "__start__" in out
    assert "echo" in out


def test_mermaid_static_edge_to_end() -> None:
    out = json_to_mermaid(_simple_config())
    assert "__end__" in out


def test_mermaid_conditional_edge_labels() -> None:
    out = json_to_mermaid(_conditional_config())
    assert "|gather|" in out
    assert "|respond|" in out


def test_mermaid_output_ends_with_newline() -> None:
    out = json_to_mermaid(_simple_config())
    assert out.endswith("\n")


def test_mermaid_accepts_graph_config_object() -> None:
    from dlg._config import GraphConfig

    cfg = GraphConfig.model_validate(_simple_config())
    out = json_to_mermaid(cfg)
    assert "flowchart TD" in out


# --- convert_json_to_mmd ---


def test_convert_json_to_mmd_creates_file(tmp_path: Path) -> None:
    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mmd_path = convert_json_to_mmd(json_path)

    assert mmd_path == tmp_path / "graph.mmd"
    assert mmd_path.exists()


def test_convert_json_to_mmd_content(tmp_path: Path) -> None:
    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mmd_path = convert_json_to_mmd(json_path)
    content = mmd_path.read_text(encoding="utf-8")

    assert "flowchart TD" in content
    assert "echo" in content


def test_convert_json_to_mmd_accepts_str_path(tmp_path: Path) -> None:
    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mmd_path = convert_json_to_mmd(str(json_path))
    assert mmd_path.suffix == ".mmd"


def test_convert_json_to_mmd_same_directory(tmp_path: Path) -> None:
    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mmd_path = convert_json_to_mmd(json_path)
    assert mmd_path.parent == tmp_path


# --- convert_mmd_to_image ---


def test_convert_mmd_to_image_calls_mmdc(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    # Force mmdc branch regardless of environment
    with patch("shutil.which", return_value="/usr/bin/mmdc"):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            out = convert_mmd_to_image(mmd_path, "png")

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "mmdc"
    assert "-i" in args
    assert "-o" in args
    assert out == tmp_path / "graph.png"


def test_convert_mmd_to_image_falls_back_to_npx(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    # mmdc not on PATH -> npx fallback
    with patch("shutil.which", return_value=None):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            convert_mmd_to_image(mmd_path, "png")

    args = mock_run.call_args[0][0]
    assert args[0] == "npx"
    assert "@mermaid-js/mermaid-cli" in args


def test_convert_mmd_to_image_default_format_is_png(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        out = convert_mmd_to_image(mmd_path)

    assert out.suffix == ".png"


def test_convert_mmd_to_image_svg_format(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        out = convert_mmd_to_image(mmd_path, "svg")

    assert out.suffix == ".svg"


def test_convert_mmd_to_image_raises_on_mmdc_failure(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "mmdc: command not found"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="mmdc failed"):
            convert_mmd_to_image(mmd_path, "png")


def test_convert_mmd_to_image_accepts_str_path(tmp_path: Path) -> None:
    mmd_path = tmp_path / "graph.mmd"
    mmd_path.write_text("flowchart TD\n    A --> B\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        out = convert_mmd_to_image(str(mmd_path), "jpg")

    assert out.suffix == ".jpg"


# --- CLI (__main__) ---


def test_cli_generates_mmd(tmp_path: Path) -> None:
    import sys
    from unittest.mock import patch as upatch

    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    with upatch("sys.argv", ["dlg", str(json_path)]):
        from dlg.__main__ import main

        main()

    assert (tmp_path / "graph.mmd").exists()


def test_cli_generates_image_with_format_flag(tmp_path: Path) -> None:
    import sys
    from unittest.mock import patch as upatch

    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with upatch("sys.argv", ["dlg", str(json_path), "--format", "png"]):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            from dlg.__main__ import main

            main()

    mock_run.assert_called_once()


def test_cli_multiple_format_flags(tmp_path: Path) -> None:
    import sys
    from unittest.mock import patch as upatch

    json_path = tmp_path / "graph.json"
    json_path.write_text(json.dumps(_simple_config()), encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with upatch("sys.argv", ["dlg", str(json_path), "-f", "png", "-f", "svg"]):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            from dlg.__main__ import main

            main()

    assert mock_run.call_count == 2
