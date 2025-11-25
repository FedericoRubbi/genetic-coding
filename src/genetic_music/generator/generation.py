"""Utilities for generating and parsing control patterns with Lark.

This module exposes a small, tidy API:

- ``parse_control_pattern(text)`` -> Lark parse tree
- ``pattern_tree_from_string(text)`` -> :class:`PatternTree`
- ``generate_expressions(n)`` -> list of :class:`PatternTree` generated via
  Hypothesis strategies over the Lark grammar.
"""

from __future__ import annotations

import random
import warnings
from typing import Dict, List, Optional

from hypothesis import strategies as st
from hypothesis.errors import HypothesisWarning, NonInteractiveExampleWarning
from hypothesis.extra.lark import from_lark
from lark import Lark, Token, Tree

from genetic_music.tree.node import TreeNode
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
# Additional parser for subtree mutation
# ---------------------------------------------------------------------------

# For mutation we want to be able to start from many internal control rules,
# not only ``control_pattern``.  We derive the available rule names from the
# generation parser and select those belonging to the ``control`` module.
_CONTROL_RULE_NAMES = sorted(
    {
        name
        for rule in _GEN_PARSER.rules
        for name in [getattr(getattr(rule, "origin", None), "name", None)]
        if isinstance(name, str) and name.startswith("control__")
    }
)

_MUTATION_START_RULES: List[str] = [
    # Top-level control pattern entrypoint
    "control_pattern",
    # All rules that are namespaced under the imported ``control`` grammar
    *_CONTROL_RULE_NAMES,
]
_MUTATION_START_SET = set(_MUTATION_START_RULES)

# Dedicated LALR parser that accepts any of the mutation start rules.
_MUTATION_PARSER = Lark.open(
    "src/genetic_music/grammar/main.lark",
    start=_MUTATION_START_RULES,
    parser="lalr",
    lexer="contextual",
)


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
    print(f"Making explicit for {gen_lark}")
    term_names = {t.name for t in gen_lark.terminals}
    explicit = {}
    for base, strat in base_to_strategy.items():
        matches = [n for n in term_names if n == base or n.endswith("__" + base)]
        if not matches:
            # print(f"No matches for {base}")
            continue
        for m in matches:
            # print(f"Adding {m} = {strat}")
            explicit[m] = strat
    print(f"Explicit: {explicit}")
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


# Cache of per-rule generative strategies (rule name -> strategy yielding strings)
_RULE_STRATEGIES: Dict[str, Optional[st.SearchStrategy[str]]] = {}


def _strategy_for_rule(rule_name: str) -> Optional[st.SearchStrategy[str]]:
    """Return (and cache) a Hypothesis strategy that generates strings for a rule.

    The strategy samples strings that are valid derivations of the given
    non-terminal ``rule_name`` according to the LALR grammar used for
    mutation.  Returns ``None`` if such a strategy cannot be constructed.
    """
    # Only attempt to build a strategy for rules that are valid mutation
    # entrypoints for the dedicated mutation parser.
    if rule_name not in _MUTATION_START_SET:
        print(f"Rule {rule_name} is not a valid mutation start rule")
        print(f"Valid mutation start rules: {_MUTATION_START_SET}")
        return None

    if rule_name in _RULE_STRATEGIES:
        print(f"Returning cached strategy for rule {rule_name}")
        print(f"Cached strategy: {_RULE_STRATEGIES[rule_name]}")
        return _RULE_STRATEGIES[rule_name]

    try:
        strat: st.SearchStrategy[str] = from_lark(
            _MUTATION_PARSER,
            start=rule_name,
            explicit=_EXPLICIT,
            alphabet=_ALPHABET_STRATEGY,
        )
    except Exception as e:
        print(f"Error building strategy for rule {rule_name}: {e}")
        strat = None  # type: ignore[assignment]

    _RULE_STRATEGIES[rule_name] = strat
    return strat


def generate_subtree_for_rule(
    rule_name: str, max_attempts: int = 20
) -> Optional[TreeNode]:
    """Generate a new subtree for the given grammar rule.

    This uses Hypothesis' Lark integration to draw example strings from the
    grammar starting at ``rule_name``, then parses them back into a Lark tree
    (also starting at ``rule_name``) and converts that into a ``TreeNode`` tree.
    If no valid example can be found within ``max_attempts`` draws, returns
    ``None``.
    """
    strat = _strategy_for_rule(rule_name)
    if strat is None:
        return None

    for _ in range(max_attempts):
        # Draw a candidate string for this rule.
        text = strat.example()
        if not isinstance(text, str) or not text.strip():
            print(f"Error generating {text} for rule {rule_name}: Text is not a string or is empty")
            continue

        try:
            # Parse the subtree starting from this rule.
            parsed = _MUTATION_PARSER.parse(text, start=rule_name)
        except Exception as e:
            print(f"Error parsing {text} for rule {rule_name}: {e}")
            continue

        ptree = PatternTree.from_lark_tree(parsed)
        return ptree.root

    return None


def _no_empty_cp_list(tree: Tree) -> bool:
    """Disallow empty ``cp_list`` like ``randcat []``."""
    for st_tree in tree.iter_subtrees_topdown():
        if st_tree.data == "cp_list" and len(st_tree.children) == 0:
            return False
    return True


# ---------------------------------------------------------------------------
# Tree mutation helpers
# ---------------------------------------------------------------------------

def _iter_nodes_with_paths(
    root: TreeNode, path_prefix: Optional[List[int]] = None
) -> List[tuple[List[int], TreeNode]]:
    """Return a list of (path, node) pairs for all nodes in the tree.

    ``path`` is a list of child indices from the root to the node.
    """
    if path_prefix is None:
        path_prefix = []

    results: List[tuple[List[int], TreeNode]] = []

    def _walk(node: TreeNode, path: List[int]) -> None:
        results.append((path, node))
        for idx, child in enumerate(node.children):
            _walk(child, path + [idx])

    _walk(root, path_prefix)
    return results


def _clone_with_replacement(
    node: TreeNode, path: List[int], new_subtree: TreeNode
) -> TreeNode:
    """Clone ``node`` while replacing the node at ``path`` with ``new_subtree``."""
    if not path:
        # We are at the target node; replace entirely.
        return new_subtree

    idx = path[0]
    # Clone current node with potentially replaced child.
    new_children: List[TreeNode] = []
    for i, child in enumerate(node.children):
        if i == idx:
            new_children.append(_clone_with_replacement(child, path[1:], new_subtree))
        else:
            # Shallow copy of unaffected children is fine; they are immutable for our purposes.
            new_children.append(child)

    return TreeNode(op=node.op, children=new_children, value=node.value)


def mutate_pattern_tree(tree: PatternTree) -> PatternTree:
    """Return a new :class:`PatternTree` with one subtree replaced.

    A node is chosen uniformly at random among all nodes in the tree, and its
    ``op`` is used as the grammar rule name for generating a new subtree via
    :func:`generate_subtree_for_rule`.  If subtree generation fails, the
    original tree is returned unchanged.
    """
    # Restrict mutation targets to nodes whose ``op`` is a valid mutation
    # start rule for our dedicated mutation parser.
    candidate_nodes = [
        (path, node)
        for path, node in _iter_nodes_with_paths(tree.root)
        if node.op in _MUTATION_START_SET
    ]
    if not candidate_nodes:
        return tree

    path, target = random.choice(candidate_nodes)

    # Attempt to generate a replacement subtree using the node's op as rule name.
    new_subtree = generate_subtree_for_rule(target.op)
    if new_subtree is None:
        return tree

    new_root = _clone_with_replacement(tree.root, path, new_subtree)
    return PatternTree(root=new_root)


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
        pretty = raw
        # pretty = _pretty_with_spaces(raw)
        # if len(pretty) <= 20:
        #     continue
        try:
            parsed = _EARLEY_PARSER.parse(pretty)
        except Exception as e:
            print(f"Error parsing {pretty}: {e}")
            continue
        # if not _no_empty_cp_list(parsed):
        #     continue

        results.append(PatternTree.from_lark_tree(parsed))

    return results
