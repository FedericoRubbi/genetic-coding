from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


SymbolKind = str  # "nonterminal" | "terminal" | "unknown"
EdgeKind = str  # "production" | "file-owns" | "import" | "alias"


@dataclass
class RuleDef:
    name: str  # canonical symbol name (without ?/! prefixes)
    raw_name: str  # original name as it appears in the grammar
    kind: SymbolKind
    file: Path
    line: int
    definition: str
    references: Set[str] = field(default_factory=set)


@dataclass
class SymbolNode:
    name: str
    kind: SymbolKind
    file: Optional[Path] = None
    rules: List[RuleDef] = field(default_factory=list)

    def add_rule(self, rule: RuleDef) -> None:
        self.rules.append(rule)
        # Prefer the first defining file, but fall back to any
        if self.file is None:
            self.file = rule.file


@dataclass
class Edge:
    src: str  # symbol name or file id
    dst: str  # symbol name or file id
    kind: EdgeKind


@dataclass
class GrammarGraph:
    symbols: Dict[str, SymbolNode] = field(default_factory=dict)
    files: Set[Path] = field(default_factory=set)
    edges: List[Edge] = field(default_factory=list)

    def ensure_symbol(
        self, name: str, kind: SymbolKind = "unknown", file: Optional[Path] = None
    ) -> SymbolNode:
        node = self.symbols.get(name)
        if node is None:
            node = SymbolNode(name=name, kind=kind, file=file)
            self.symbols[name] = node
        else:
            # Upgrade unknown kind if we discover a more specific one
            if node.kind == "unknown" and kind != "unknown":
                node.kind = kind
            if node.file is None and file is not None:
                node.file = file
        return node

    def add_edge(self, src: str, dst: str, kind: EdgeKind) -> None:
        self.edges.append(Edge(src=src, dst=dst, kind=kind))


def classify_symbol_kind(name: str) -> SymbolKind:
    """
    Heuristic classification:
      - ALL CAPS (with digits/underscores) => terminal
      - otherwise => nonterminal
    """
    base = name.strip()
    if not base:
        return "unknown"
    if base.upper() == base and any(ch.isalpha() for ch in base):
        return "terminal"
    return "nonterminal"


