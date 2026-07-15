from __future__ import annotations

import argparse
import sys
from pathlib import Path

import opendataloader_pdf


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_ROOT / "paper" / "GELMA" / "Small - 2024 - Yuan - Injectable GelMA Hydrogel Microspheres with Sustained Release of Platelet‐Rich Plasma for the.pdf"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "markdown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a PDF paper to Markdown with opendataloader_pdf."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the input PDF file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory used to store converted files.",
    )
    parser.add_argument(
        "--format",
        default="markdown",
        help="Output format passed to opendataloader_pdf, e.g. markdown or markdown,json.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()

    if not input_path.exists():
        print(f"Input PDF not found: {input_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        opendataloader_pdf.convert(
            input_path=[str(input_path)],
            output_dir=str(output_dir),
            format=args.format,
        )
    except FileNotFoundError as exc:
        print(
            "Conversion failed because Java was not found. "
            "Please make sure `java` is installed and available in PATH.",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - CLI fallback path
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1

    print(f"Converted {input_path.name} to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
