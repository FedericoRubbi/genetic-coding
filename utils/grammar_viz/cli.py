from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import build_symbol_graph, parse_grammar_file
from .html_view import render_html_graph
from .scanner import discover_grammar_files, iter_grammar_files


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize Lark grammars as an interactive HTML graph."
    )
    parser.add_argument(
        "--root",
        default="src/genetic_music/grammar",
        help="Root folder for grammar files (default: %(default)s).",
    )
    parser.add_argument(
        "--entry",
        default=None,
        help="Optional entry .lark file (relative to --root or absolute). "
        "If provided, only grammars reachable via %%import from this file are included.",
    )
    parser.add_argument(
        "--out",
        default="data/outputs/grammar_viz/grammar_graph.html",
        help="Output HTML file path (default: %(default)s).",
    )
    parser.add_argument(
        "--hide-terminals",
        action="store_true",
        help="Hide terminal symbols to reduce graph size.",
    )
    parser.add_argument(
        "--focus",
        default=None,
        help="Optional symbol name to focus on; only a small neighborhood around "
        "this symbol is shown.",
    )
    parser.add_argument(
        "--focus-depth",
        type=int,
        default=2,
        help="Graph distance radius when using --focus (default: %(default)s).",
    )
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Do not include file nodes in the visualization.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"[ERROR] Grammar root not found: {root}")

    entry_path = Path(args.entry) if args.entry is not None else None

    files, import_graph = discover_grammar_files(root=root, entry=entry_path)
    if not files:
        raise SystemExit(f"[ERROR] No .lark files found under root: {root}")

    print(f"[grammar_viz] Discovered {len(files)} grammar files.")

    # Parse rules from all discovered grammar files
    all_rules = []
    for fp in iter_grammar_files(files):
        rules = parse_grammar_file(fp)
        all_rules.extend(rules)

    print(
        f"[grammar_viz] Parsed {len(all_rules)} rules across {len(files)} files."
    )

    graph = build_symbol_graph(all_rules)

    # Include file-level import edges
    for src, targets in import_graph.items():
        src_id = f"file:{src.as_posix()}"
        for dst in targets:
            dst_id = f"file:{dst.as_posix()}"
            graph.add_edge(src=src_id, dst=dst_id, kind="import")

    out_path = Path(args.out)
    include_files = not args.no_files

    html_path = render_html_graph(
        graph,
        out_path=out_path,
        hide_terminals=args.hide_terminals,
        include_files=include_files,
        focus=args.focus,
        focus_depth=args.focus_depth,
    )

    print(f"[grammar_viz] Wrote HTML graph to: {html_path}")


