"""Utilities for generating and parsing control patterns with Lark.

This module exposes a small, tidy API:

- ``parse_control_pattern(text)`` -> Lark parse tree
- ``pattern_tree_from_string(text)`` -> :class:`PatternTree`
- ``generate_expressions(n)`` -> list of :class:`PatternTree` generated via
  Hypothesis strategies over the Lark grammar.
"""

from __future__ import annotations

import warnings
from typing import List

from hypothesis import strategies as st
from hypothesis.errors import HypothesisWarning, NonInteractiveExampleWarning
from hypothesis.extra.lark import from_lark
from lark import Lark, Token, Tree

from genetic_music.tree.pattern_tree import PatternTree

# Silence Hypothesis warnings when using strategies as a data generator.
warnings.filterwarnings("ignore", category=NonInteractiveExampleWarning)
warnings.filterwarnings("ignore", category=HypothesisWarning)


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

def _build_parsers() -> tuple[Lark, Lark]:
    """Build the Earley (validation) and LALR (generation) parsers."""
    # Load grammar from the file path under ``src/genetic_music/grammar`` so that
    # the grammar files live alongside the code without relying on package
    # resource loading (which can interact poorly with Lark's %import resolution).
    earley = Lark.open(
        "src/genetic_music/grammar/main.lark",
        start="control_pattern",  # playable by construction
    )
    gen = Lark.open(
        "src/genetic_music/grammar/main.lark",
        start="control_pattern",  # playable by construction
        parser="lalr",
        lexer="contextual",
    )
    return earley, gen


_EARLEY_PARSER, _GEN_PARSER = _build_parsers()


# ---------------------------------------------------------------------------
# Token pretty-printing helpers
# ---------------------------------------------------------------------------

def _needs_space(prev: Token, cur: Token) -> bool:
    """Heuristic for inserting spaces between tokens for readability."""
    if prev.value.endswith('"') or cur.value.startswith('"'):
        return False
    if prev.value and prev.value[-1] in "([{|,":
        return False
    if cur.value and cur.value[0] in ")]}|,:":
        return False
    return (prev.value and prev.value[-1].isalnum()) and (
        cur.value and cur.value[0].isalnum()
    )


def _pretty_with_spaces(s: str) -> str:
    """Re-lex a raw string and insert spaces where appropriate."""
    toks = list(_GEN_PARSER.lex(s, dont_ignore=True))
    toks = [t for t in toks if t.type not in getattr(_GEN_PARSER, "ignore_tokens", ())]
    out = []
    for i, t in enumerate(toks):
        if i and _needs_space(toks[i - 1], t):
            out.append(" ")
        out.append(t.value)
    return "".join(out)


# ---------------------------------------------------------------------------
# Hypothesis strategy for valid control_pattern strings
# ---------------------------------------------------------------------------

def _make_explicit(gen_lark: Lark, base_to_strategy):
    term_names = {t.name for t in gen_lark.terminals}
    explicit = {}
    for base, strat in base_to_strategy.items():
        matches = [n for n in term_names if n == base or n.endswith("__" + base)]
        if not matches:
            continue
        for m in matches:
            explicit[m] = strat
    return explicit


_BASE_EXPLICIT = {
    # Finite string domains
    "SAMPLE_STRING": st.sampled_from(['"bd"', '"sn"', '"hh"', '"tabla"']),
    "VOWEL_STRING": st.sampled_from(['"a"', '"e"', '"i"', '"o"', '"u"']),
    "SCALE_STRING": st.sampled_from(['"minor"', '"major"', '"dorian"']),
    "PARAM_STRING": st.sampled_from(['"pan"', '"gain"', '"shape"', '"cutoff"']),
    "BUS_STRING": st.sampled_from(['"gain"', '"speed"', '"pan"']),
    # Keep numbers small/readable
    "INT": st.integers(min_value=0, max_value=12).map(str),
    "DOUBLE": st.floats(
        min_value=0, max_value=8, allow_nan=False, allow_infinity=False
    ).map(lambda x: f"{x:.2f}"),
}

# Use the parser's ignore tokens to define whitespace behaviour
_BASE_EXPLICIT["SILENCE"] = st.nothing()
for name in getattr(_GEN_PARSER, "ignore_tokens", ()):
    if name == "WS":
        _BASE_EXPLICIT[name] = st.just(" ")
    else:
        _BASE_EXPLICIT[name] = st.just("")

_BASE_EXPLICIT.update(
    {
        "WS": st.just(" "),
    }
)

_EXPLICIT = _make_explicit(_GEN_PARSER, _BASE_EXPLICIT)

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\"()"
_ALPHABET_STRATEGY = st.sampled_from(list(_ALPHABET))

_CP_STRINGS = from_lark(
    _GEN_PARSER,
    start="control_pattern",
    explicit=_EXPLICIT,
    alphabet=_ALPHABET_STRATEGY,
)


def _no_empty_cp_list(tree: Tree) -> bool:
    """Disallow empty ``cp_list`` like ``randcat []``."""
    for st_tree in tree.iter_subtrees_topdown():
        if st_tree.data == "cp_list" and len(st_tree.children) == 0:
            return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_control_pattern(text: str) -> Tree:
    """Parse a textual control pattern into a Lark parse tree."""
    return _EARLEY_PARSER.parse(text)


def pattern_tree_from_string(text: str) -> PatternTree:
    """Convenience: parse a string and convert it into a :class:`PatternTree`."""
    tree = parse_control_pattern(text)
    return PatternTree.from_lark_tree(tree)


def generate_expressions(n: int = 10) -> List[PatternTree]:
    """Generate ``n`` random control patterns as :class:`PatternTree` objects.

    This uses Hypothesis' Lark integration on the LALR+contextual parser to
    sample syntax-valid strings, then:

    1. Re-inserts human-friendly spacing.
    2. Validates with the Earley parser.
    3. Filters out degenerate structures (e.g., empty ``cp_list``).
    4. Converts the resulting parse tree into a :class:`PatternTree`.
    """
    results: List[PatternTree] = []

    while len(results) < n:
        raw = _CP_STRINGS.example()
        if not raw.strip():
            continue
        pretty = _pretty_with_spaces(raw)
        if len(pretty) <= 20:
            continue
        try:
            parsed = _EARLEY_PARSER.parse(pretty)
        except Exception:
            continue
        if not _no_empty_cp_list(parsed):
            continue

        results.append(PatternTree.from_lark_tree(parsed))

    return results
