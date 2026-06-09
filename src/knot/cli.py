"""Command-line interface for knot."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from knot import __version__
from knot.analyzer import build_graph
from knot.graph import find_cycles
from knot.render import render

EXIT_OK = 0
EXIT_CYCLES_FOUND = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knot",
        description="Detect and visualize circular imports in Python projects.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="file, package, or project directory to analyze (default: .)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("text", "json", "mermaid"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="directory name to exclude (repeatable)",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="always exit 0, even when cycles are found",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        graph = build_graph(args.path, excludes=args.exclude)
    except FileNotFoundError:
        print(f"knot: path not found: {args.path}", file=sys.stderr)
        return EXIT_ERROR

    cycles = find_cycles(graph.edges)
    print(render(args.format, graph, cycles))

    if cycles and not args.no_fail:
        return EXIT_CYCLES_FOUND
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
