"""CLI: python -m dlg <json_path> [--format png] [--output-dir DIR] ..."""
from __future__ import annotations

import argparse
import sys

from dlg.mermaid import convert_json_to_mmd, convert_mmd_to_image


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dlg",
        description="Convert DLG JSON graph config to Mermaid (.mmd) and optionally to image formats.",
    )
    parser.add_argument("json_path", help="Path to the graph JSON file")
    parser.add_argument(
        "--format",
        "-f",
        dest="formats",
        action="append",
        metavar="FORMAT",
        help="Output image format (png, svg, jpg, pdf). Repeatable. Requires mmdc or npx.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        dest="output_dir",
        default=None,
        metavar="DIR",
        help="Directory for generated image files (default: same dir as input JSON).",
    )
    args = parser.parse_args()

    mmd_path = convert_json_to_mmd(args.json_path)
    print(f"Written: {mmd_path}")

    for fmt in args.formats or []:
        out = convert_mmd_to_image(mmd_path, fmt, output_dir=args.output_dir)
        print(f"Written: {out}")


if __name__ == "__main__":
    sys.exit(main())
