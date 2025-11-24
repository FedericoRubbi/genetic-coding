from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple

from utils.check_lark_import_dag import build_import_graph


ImportGraph = Dict[Path, Set[Path]]


def discover_grammar_files(
    root: Path, entry: Optional[Path] = None
) -> Tuple[Set[Path], ImportGraph]:
    """
    Discover .lark grammar files starting from a root directory.

    If ``entry`` is provided, only files reachable from that entry via %import
    edges are returned (plus the entry itself). Otherwise, all .lark files
    under ``root`` are scanned.
    """
    root = root.resolve()
    entry_resolved: Optional[Path]
    if entry is not None:
        entry_resolved = (root / entry).resolve() if not entry.is_absolute() else entry.resolve()
    else:
        entry_resolved = None

    graph, _unresolved = build_import_graph(root=root, entry=entry_resolved)

    files: Set[Path] = set()
    for src, targets in graph.items():
        files.add(src)
        files.update(targets)

    return files, graph


def iter_grammar_files(files: Set[Path]) -> Iterable[Path]:
    """Yield grammar files in a stable, sorted order."""
    for p in sorted(files):
        if p.suffix == ".lark":
            yield p


