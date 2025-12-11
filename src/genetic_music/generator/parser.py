from __future__ import annotations

"""Parser construction and utilities for Tidal control patterns.

This module owns the Lark parser instances used throughout the
:mod:`genetic_music.generator` package.
"""

from typing import Tuple

from lark import Lark, Token, Tree


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def _build_parsers() -> Tuple[Lark, Lark]:
    """Build the Earley (validation) and LALR (generation) parsers.

    The grammar is loaded from ``src/genetic_music/grammar/main.lark`` so
    that the grammar files live alongside the code without relying on
    package resource loading (which can interact poorly with Lark's
    ``%import`` resolution).
    """

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


def get_parsers() -> Tuple[Lark, Lark]:
    """Return the cached (Earley, LALR) parser instances."""

    return _EARLEY_PARSER, _GEN_PARSER


def parse_control_pattern(text: str) -> Tree:
    """Parse a textual control pattern into a Lark parse tree."""

    return _EARLEY_PARSER.parse(text)


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


def pretty_with_spaces(s: str) -> str:
    """Re-lex a raw string and insert spaces where appropriate."""

    toks = list(_GEN_PARSER.lex(s, dont_ignore=True))
    toks = [t for t in toks if t.type not in getattr(_GEN_PARSER, "ignore_tokens", ())]
    out: list[str] = []
    for i, t in enumerate(toks):
        if i and _needs_space(toks[i - 1], t):
            out.append(" ")
        out.append(t.value)
    return "".join(out)
