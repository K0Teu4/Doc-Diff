from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .differ import Differ
from .embedder import Embedder
from .formatter import Formatter
from .html_generator import HtmlGenerator
from .matcher import Matcher
from .parser import parse_docx


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docdiff",
        description="Semantic document diff for DOCX files.",
    )
    parser.add_argument("old_doc", type=str, help="Path to the old DOCX file.")
    parser.add_argument("new_doc", type=str, help="Path to the new DOCX file.")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path. For html, defaults to docdiff-report.html. For others, stdout.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Cosine similarity threshold for block matching (default: 0.75).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device for sentence-transformers model (cpu, cuda, etc.).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)

    old_path = Path(args.old_doc)
    new_path = Path(args.new_doc)

    if not old_path.exists():
        print(f"Error: file not found: {old_path}", file=sys.stderr)
        return 1
    if not new_path.exists():
        print(f"Error: file not found: {new_path}", file=sys.stderr)
        return 1

    print("Parsing documents...", file=sys.stderr)
    blocks_old = parse_docx(old_path)
    blocks_new = parse_docx(new_path)

    print("Loading embedding model...", file=sys.stderr)
    embedder = Embedder(device=args.device)
    matcher = Matcher(embedder, threshold=args.threshold)
    differ = Differ()
    formatter = Formatter(differ)
    html_generator = HtmlGenerator(differ)

    print("Matching semantic blocks...", file=sys.stderr)
    match_result = matcher.match(blocks_old, blocks_new)

    output_text = ""
    if args.format == "json":
        output_text = formatter.to_json_string(match_result)
    elif args.format == "html":
        output_text = html_generator.generate(match_result)
    else:
        output_text = formatter.format_markdown(match_result)

    output_path = args.output
    if args.format == "html" and not output_path:
        output_path = "docdiff-report.html"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Report saved to: {output_path}", file=sys.stderr)
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
