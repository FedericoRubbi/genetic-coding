from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Set

from .graph_model import GrammarGraph, SymbolNode


def _try_import_pyvis():
    try:
        from pyvis.network import Network  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise RuntimeError(
            "The 'pyvis' package is required to render the grammar HTML graph. "
            "Install it with `pip install pyvis`."
        ) from exc
    return Network


def _visible_symbols(
    graph: GrammarGraph, hide_terminals: bool
) -> Set[str]:
    visible: Set[str] = set()
    for name, node in graph.symbols.items():
        if hide_terminals and node.kind == "terminal":
            continue
        visible.add(name)
    return visible


def _visible_edges(
    graph: GrammarGraph,
    visible_symbols: Set[str],
    include_files: bool,
) -> Iterable[tuple[str, str, str]]:
    for edge in graph.edges:
        if edge.kind == "production":
            # src/dst are sym:NAME
            src_name = edge.src.removeprefix("sym:")
            dst_name = edge.dst.removeprefix("sym:")
            if src_name in visible_symbols and dst_name in visible_symbols:
                yield edge.src, edge.dst, edge.kind
        elif edge.kind == "file-owns" and include_files:
            # Only include ownership edges for visible symbol nodes
            dst_name = edge.dst.removeprefix("sym:")
            if dst_name in visible_symbols:
                yield edge.src, edge.dst, edge.kind
        elif edge.kind == "import" and include_files:
            # File-to-file edges are always OK if file nodes are enabled
            yield edge.src, edge.dst, edge.kind


def _node_style_for_symbol(node: SymbolNode) -> dict:
    if node.kind == "terminal":
        color = "#ffcc66"
        shape = "ellipse"
    elif node.kind == "nonterminal":
        color = "#66ccff"
        shape = "dot"
    else:
        color = "#cccccc"
        shape = "dot"

    # Plain-text tooltip: easier to read than raw HTML markup in the UI
    title_lines = [f"{node.name} ({node.kind})"]
    if node.file is not None:
        title_lines.append(str(node.file))
    if node.rules:
        # Show a short snippet of the first rule
        snippet = node.rules[0].definition.replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."
        if snippet:
            title_lines.append(snippet)

    return {
        "color": color,
        "shape": shape,
        "title": "".join(title_lines),
        "size": 15 if node.kind != "terminal" else 10,
    }


def render_html_graph(
    graph: GrammarGraph,
    out_path: Path,
    hide_terminals: bool = False,
    include_files: bool = True,
    focus: Optional[str] = None,
    focus_depth: int = 2,
) -> Path:
    """
    Render the GrammarGraph to an interactive HTML file using pyvis.
    """
    Network = _try_import_pyvis()

    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#111111",
        font_color="#f0f0f0",
        directed=True,
    )
    net.toggle_physics(True)

    visible_symbols = _visible_symbols(graph, hide_terminals=hide_terminals)

    # Optional focus subgraph (BFS on symbol nodes)
    if focus is not None and focus in visible_symbols:
        from collections import deque

        queue: deque[tuple[str, int]] = deque()
        queue.append((focus, 0))
        keep: Set[str] = set()
        keep.add(focus)

        adjacency: dict[str, set[str]] = {}
        for edge in graph.edges:
            if edge.kind != "production":
                continue
            src_name = edge.src.removeprefix("sym:")
            dst_name = edge.dst.removeprefix("sym:")
            adjacency.setdefault(src_name, set()).add(dst_name)
            adjacency.setdefault(dst_name, set()).add(src_name)

        while queue:
            name, depth = queue.popleft()
            if depth >= focus_depth:
                continue
            for neigh in adjacency.get(name, ()):
                if neigh in visible_symbols and neigh not in keep:
                    keep.add(neigh)
                    queue.append((neigh, depth + 1))

        visible_symbols = keep

    # Add symbol nodes
    for name, node in graph.symbols.items():
        if name not in visible_symbols:
            continue
        node_id = f"sym:{name}"
        style = _node_style_for_symbol(node)
        net.add_node(
            node_id,
            label=name,
            **style,
        )

    # Add file nodes
    if include_files:
        for f in sorted(graph.files):
            node_id = f"file:{f.as_posix()}"
            label = f.name
            # Plain-text tooltip for file nodes
            title = f"{f.name}\n{f}"
            net.add_node(
                node_id,
                label=label,
                title=title,
                shape="box",
                color="#8888ff",
                size=18,
            )

    # Add edges
    for src, dst, kind in _visible_edges(
        graph, visible_symbols=visible_symbols, include_files=include_files
    ):
        color = "#aaaaaa"
        if kind == "production":
            color = "#bbbbbb"
        elif kind == "file-owns":
            color = "#8888ff"
        elif kind == "import":
            color = "#ff8888"

        net.add_edge(src, dst, color=color)

    net.show_buttons(filter_=["physics"])
    net.save_graph(str(out_path))
    return out_path


