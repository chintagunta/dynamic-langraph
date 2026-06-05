from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dlg._config import GraphConfig


def json_to_mermaid(config: dict[str, Any] | GraphConfig) -> str:
    if isinstance(config, GraphConfig):
        cfg = config
    else:
        cfg = GraphConfig.model_validate(config)

    lines: list[str] = ["flowchart TD"]

    entry = cfg.edges.entry_point
    lines.append(f"    __start__((__start__)) --> {entry}")

    for edge in cfg.edges.static_edges:
        to = edge.to_node
        if to == "__end__":
            lines.append(f"    {edge.from_node} --> __end__((__end__))")
        else:
            lines.append(f"    {edge.from_node} --> {to}")

    for cedge in cfg.edges.conditional_edges:
        if cedge.path_map:
            for label, target in cedge.path_map.items():
                to = target
                if to == "__end__":
                    lines.append(f"    {cedge.from_node} -->|{label}| __end__((__end__))")
                else:
                    lines.append(f"    {cedge.from_node} -->|{label}| {to}")
        else:
            lines.append(f"    {cedge.from_node} -->|route| ...")

    return "\n".join(lines) + "\n"


def convert_json_to_mmd(json_path: str | Path) -> Path:
    p = Path(json_path)
    with p.open() as f:
        data = json.load(f)
    mmd_path = p.with_suffix(".mmd")
    mmd_path.write_text(json_to_mermaid(data), encoding="utf-8")
    return mmd_path


def convert_mmd_to_image(
    mmd_path: str | Path,
    output_format: str = "png",
    output_dir: str | Path | None = None,
) -> Path:
    """Convert a .mmd file to an image using mmdc (falls back to npx mmdc).

    Requires either mmdc on PATH (npm i -g @mermaid-js/mermaid-cli)
    or npx available (included with Node.js).
    """
    import shutil
    import subprocess

    mmd_path = Path(mmd_path)
    if output_dir is not None:
        out_path = Path(output_dir) / f"{mmd_path.stem}.{output_format}"
    else:
        out_path = mmd_path.with_suffix(f".{output_format}")

    cmd_base = (
        ["mmdc"] if shutil.which("mmdc") else ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    )
    result = subprocess.run(
        [*cmd_base, "-i", str(mmd_path), "-o", str(out_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"mmdc failed: {result.stderr.strip()}")
    return out_path
