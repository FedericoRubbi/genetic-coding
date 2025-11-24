from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Set

from utils.check_lark_import_dag import strip_line_comment

from .graph_model import GrammarGraph, RuleDef, classify_symbol_kind


RULE_DEF_RE = re.compile(
    r"""^\s*
        (?P<name>[?*!]?[A-Za-z_][A-Za-z0-9_]*)
        \s*:
    """,
    re.VERBOSE,
)

IDENT_RE = re.compile(r"[?*!]?[A-Za-z_][A-Za-z0-9_]*")


def _strip_strings_and_regex(s: str) -> str:
    """
    Remove string/regex literals from a grammar RHS so we don't mistake them
    for symbol references.
    """
    out: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in {'"', "'"}:
            quote = ch
            out.append(" ")
            i += 1
            while i < n:
                c = s[i]
                if c == "\\":
                    i += 2
                elif c == quote:
                    i += 1
                    break
                else:
                    i += 1
        elif ch == "/":
            # Assume /.../ is a regex literal (comments have been stripped)
            out.append(" ")
            i += 1
            while i < n:
                c = s[i]
                if c == "\\":
                    i += 2
                elif c == "/":
                    i += 1
                    break
                else:
                    i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def extract_references(rhs: str) -> Set[str]:
    """
    Extract candidate symbol references from a rule body.
    This is heuristic but works well for typical Lark grammars.
    """
    cleaned = _strip_strings_and_regex(rhs)
    refs: Set[str] = set()
    for m in IDENT_RE.finditer(cleaned):
        ident = m.group(0)
        if not ident:
            continue
        # Strip ? / ! prefixes used by Lark for inline/expansion hints
        ident = ident.lstrip("!?")
        refs.add(ident)
    return refs


def parse_grammar_file(path: Path) -> List[RuleDef]:
    """
    Parse a single .lark file into RuleDef objects.
    """
    rules: List[RuleDef] = []
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    current_name: str | None = None
    current_raw_name: str | None = None
    current_kind: str | None = None
    current_line: int | None = None
    body_lines: List[str] = []

    def flush_rule() -> None:
        nonlocal current_name, current_raw_name, current_kind, current_line, body_lines
        if current_name is None or current_raw_name is None or current_kind is None or current_line is None:
            body_lines = []
            return
        definition = "\n".join(body_lines).strip()
        refs = extract_references(definition) if definition else set()
        rules.append(
            RuleDef(
                name=current_name,
                raw_name=current_raw_name,
                kind=current_kind,
                file=path,
                line=current_line,
                definition=definition,
                references=refs,
            )
        )
        current_name = None
        current_raw_name = None
        current_kind = None
        current_line = None
        body_lines = []

    for idx, raw in enumerate(text, 1):
        no_comment = strip_line_comment(raw)
        stripped = no_comment.strip()

        # Skip pure comments
        if not stripped:
            # treat blank line as a rule boundary
            flush_rule()
            continue

        if stripped.startswith("%"):
            # Directives (%import, %ignore, ...) are not rule bodies
            flush_rule()
            continue

        m = RULE_DEF_RE.match(no_comment)
        if m:
            # Starting a new rule
            flush_rule()
            raw_name = m.group("name")
            canonical = raw_name.lstrip("!?")
            kind = classify_symbol_kind(canonical)
            current_name = canonical
            current_raw_name = raw_name
            current_kind = kind
            current_line = idx
            rhs = no_comment[m.end() :].strip()
            body_lines = [rhs] if rhs else []
            continue

        # Continuation of the current rule (typically lines starting with '|')
        if current_name is not None:
            body_lines.append(stripped)
        # else: line outside a rule, ignore

    # Last rule in file
    flush_rule()
    return rules


def build_symbol_graph(rules: Iterable[RuleDef]) -> GrammarGraph:
    """
    Build a symbol-level GrammarGraph from a collection of RuleDef objects.
    """
    graph = GrammarGraph()

    # First pass: declare symbol nodes and file nodes
    for rule in rules:
        graph.files.add(rule.file)
        node = graph.ensure_symbol(rule.name, kind=rule.kind, file=rule.file)
        node.add_rule(rule)

    # Add file->symbol ownership edges
    for symbol in graph.symbols.values():
        if symbol.file is not None:
            src_id = f"file:{symbol.file.as_posix()}"
            graph.files.add(symbol.file)
            graph.add_edge(src=src_id, dst=f"sym:{symbol.name}", kind="file-owns")

    # Second pass: production edges between symbols
    for rule in rules:
        src_id = f"sym:{rule.name}"
        for ref in sorted(rule.references):
            target_kind = classify_symbol_kind(ref)
            graph.ensure_symbol(ref, kind=target_kind)
            dst_id = f"sym:{ref}"
            graph.add_edge(src=src_id, dst=dst_id, kind="production")

    return graph


