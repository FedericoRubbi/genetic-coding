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
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from hypothesis import HealthCheck, Phase, given, settings, target
from hypothesis import strategies as st
from hypothesis.errors import HypothesisWarning, NonInteractiveExampleWarning
from hypothesis.extra.lark import from_lark
from lark import Lark, Token, Tree

from genetic_music.codegen.tidal_codegen import to_tidal
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
    # print(f"Explicit: {explicit}")
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

# ---------------------------------------------------------------------------
# Shared finite musical value pools for mutation operators
# ---------------------------------------------------------------------------

_SOUND_POOL = ["bd", "sn", "hh", "cp", "tabla", "arpy"]

_NOTE_PATTERN_POOL = [
    "0",
    "0 7",
    "0 4 7",
    "0 2 4 5 7 9 11",
    "0 .. 11",
    "-12 .. 12",
    "24 36 48",
    "60",
    "60 64 67",
    "0.5",
    "1.5",
]

_SCALE_NAME_POOL = ["major", "minor", "dorian", "ritusen"]

_SCALE_INT_PATTERN_POOL = ["0", "0 2 4", "0 .. 7"]

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\"()[],.|*+/%#<>~{}:"
_ALPHABET_STRATEGY = st.sampled_from(list(_ALPHABET))

_CP_STRINGS = from_lark(
    _GEN_PARSER,
    start="control_pattern",
    explicit=_EXPLICIT,
    alphabet=_ALPHABET_STRATEGY,
)


def _collect_targeted_patterns(
    n: int,
    *,
    min_length: int,
    max_examples: int,
    database: Any | None = None,
    use_tree_metrics: bool = True,
) -> List[str]:
    """Use Hypothesis' targeted search to collect up to ``n`` pattern strings.

    This helper drives the ``_CP_STRINGS`` strategy under a ``@given`` test
    with a :func:`target` call that rewards longer and structurally larger
    patterns.  It returns a list of *raw* pattern strings; callers are
    responsible for parsing and wrapping them as :class:`PatternTree`
    instances.

    The number of collected patterns may be less than ``n`` if the search
    fails to discover enough high-scoring examples within ``max_examples``.
    """

    collected: List[str] = []

    @settings(
        max_examples=max_examples,
        derandomize=False,
        database=database,
        phases=(Phase.generate, Phase.target),
        suppress_health_check=(HealthCheck.too_slow, HealthCheck.filter_too_much),
        deadline=None,
    )
    @given(p=_CP_STRINGS)
    def _explore(p: str) -> None:
        # Ensure we only work with non-empty strings.
        if not isinstance(p, str) or not p.strip():
            return

        # Primary metric: maximize textual length of the pattern.
        target(float(len(p)), label="pattern_length")

        # Optional secondary metrics on the parsed tree structure.  We only
        # bother computing these while we are still filling the collection.
        if use_tree_metrics and len(collected) < n:
            try:
                tree = parse_control_pattern(p)
                ptree = PatternTree.from_lark_tree(tree)
            except Exception:
                # Parsing failures are treated as uninteresting; we simply
                # skip structural metrics for this example.
                pass
            else:
                # Reward larger trees (more nodes) and deeper trees.
                target(float(ptree.size()), label="tree_size")
                target(float(ptree.depth()), label="tree_depth")

        # Record high-scoring candidates, favouring longer strings.
        if len(p) >= min_length and len(collected) < n:
            collected.append(p)

    # Run the Hypothesis engine once; it will execute ``_explore`` up to
    # ``max_examples`` times (or fewer if it deems the search space saturated).
    _explore()
    return collected


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
        # print(f"Valid mutation start rules: {_MUTATION_START_SET}")
        return None

    if rule_name in _RULE_STRATEGIES:
        print(f"Returning cached strategy for rule {rule_name}")
        # print(f"Cached strategy: {_RULE_STRATEGIES[rule_name]}")
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


def _collect_targeted_subtrees_for_rule(
    rule_name: str,
    *,
    n: int,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
    use_target: bool,
) -> List[TreeNode]:
    """Use targeted Hypothesis search to collect up to ``n`` subtrees for a rule.

    This works similarly to :func:`_collect_targeted_patterns`, but uses the
    per-rule strategy and mutation parser.  When ``use_target`` is ``False``,
    Hypothesis still generates examples but :func:`target` is never called,
    which makes it easy to compare performance with and without targeting.
    """
    strat = _strategy_for_rule(rule_name)
    if strat is None:
        return []

    collected: List[TreeNode] = []

    @settings(
        max_examples=max_examples,
        derandomize=False,
        database=None,
        phases=(Phase.generate, Phase.target) if use_target else (Phase.generate,),
        suppress_health_check=(HealthCheck.too_slow, HealthCheck.filter_too_much),
        deadline=None,
    )
    @given(s=strat)
    def _explore(s: str) -> None:
        try:
            if not isinstance(s, str) or not s.strip():
                return

            if use_target:
                target(float(len(s)), label="subtree_length")

            if len(collected) >= n:
                return

            try:
                parsed = _MUTATION_PARSER.parse(s, start=rule_name)
                ptree = PatternTree.from_lark_tree(parsed)
            except Exception as e:
                print(f"Error parsing {s} for rule {rule_name}: {e}")
                breakpoint()
                return

            if use_target and use_tree_metrics:
                target(float(ptree.size()), label="subtree_size")
                target(float(ptree.depth()), label="subtree_depth")

            if len(s) >= min_length and len(collected) < n:
                collected.append(ptree.root)

        except Exception as e:
            print(f"Error in _explore for rule {rule_name} with string {s}: {e}")
            breakpoint()
    try:
        _explore()
    except Exception as e:
        print(f"Error running Hypothesis explore for rule {rule_name}: {e}")
        breakpoint()
    return collected


def generate_subtree_for_rule(
    rule_name: str,
    max_attempts: int = 20,
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> Optional[TreeNode]:
    """Generate a new subtree for the given grammar rule.

    This uses Hypothesis' Lark integration to draw example strings from the
    grammar starting at ``rule_name``, then parses them back into a Lark tree
    (also starting at ``rule_name``) and converts that into a ``TreeNode`` tree.
    If no valid example can be found within ``max_attempts`` draws, returns
    ``None``.
    """
    # Optional targeted search for a high-complexity subtree.

    # if use_target:
    nodes = _collect_targeted_subtrees_for_rule(
        rule_name,
        n=1,
        min_length=min_length,
        max_examples=max_examples,
        use_tree_metrics=use_tree_metrics,
        use_target=use_target,  # targetting may be disables but we still change settings
    )
    if nodes:
        return nodes[0]

    print(f"No targeted nodes found for rule {rule_name}, falling back to simple generation")

    # Fallback: simple example-based generation as before.
    strat = _strategy_for_rule(rule_name)
    if strat is None:
        return None

    for _ in range(max_attempts):
        # Draw a candidate string for this rule.
        text = strat.example()
        if not isinstance(text, str) or not text.strip():
            print(
                f"Error generating {text} for rule {rule_name}: "
                "Text is not a string or is empty"
            )
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


MutationOp = Callable[[PatternTree, random.Random], PatternTree]


def _subtree_replace_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for the classic subtree-replacement mutation operator.

    This matches the previous behaviour of :func:`mutate_pattern_tree`: pick a
    random node, generate a new subtree starting from that node's ``op`` via
    :func:`generate_subtree_for_rule`, and clone the tree with that subtree
    replaced.  If subtree generation fails, the original tree is returned.
    """

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Restrict mutation targets to nodes whose ``op`` is a valid mutation
        # start rule for our dedicated mutation parser.
        candidate_nodes = [
            (path, node)
            for path, node in _iter_nodes_with_paths(tree.root)
            if node.op in _MUTATION_START_SET
        ]
        if not candidate_nodes:
            return tree

        path, target = rng.choice(candidate_nodes)

        # Attempt to generate a replacement subtree using the node's op as rule name.
        new_subtree = generate_subtree_for_rule(
            target.op,
            use_target=use_target,
            min_length=min_length,
            max_examples=max_examples,
            use_tree_metrics=use_tree_metrics,
        )
        if new_subtree is None:
            return tree

        new_root = _clone_with_replacement(tree.root, path, new_subtree)
        return PatternTree(root=new_root)

    return op


def _stack_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a stack-based mutation operator.

    This operator wraps the entire existing pattern in a ``stack [...]`` list,
    adding a second, randomly generated playable pattern as the new sibling.
    The result is a new pattern tree whose root corresponds to a ``stack``
    combinator, increasing structural complexity in a bottom-up way.
    """

    # The config knobs are currently unused but kept for a consistent interface
    # and future experimentation (e.g. using targeted generation for the new
    # branch).
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        new_branch_trees = generate_expressions(1)

        # Create the STACK token node
        stack_token = TreeNode(op="STACK", value="stack")
        
        # Create the cp_list_playable node containing the two patterns
        list_node = TreeNode(
            op="control__cp_list_playable",
            children=[tree.root, new_branch_trees[0].root]
        )
        
        # Create the root cp_lists_playable node
        root_node = TreeNode(
            op="control__cp_lists_playable",
            children=[stack_token, list_node]
        )

        return PatternTree(root=root_node)

    return op


# Functions used to create valid "mask" patterns for the "struct" operator, that define when events are allowed to occur
MASK_GENERATORS = [
    # Boolean mask t(a,b): a pulses across b positions
    # lambda rng: f"t({rng.randint(2,8)},{rng.choice([8,12,16])})",  # Not implemented in grammar yet
    # Boolean string mask (e.g: "t f t f f t t f f")
    lambda rng: '"' + " ".join(rng.choice(['t','f']) for _ in range(rng.randint(4,16))) + '"'
    # Binary number mask (e.g: "1 0 1 1 0 0 1")
    # lambda rng: '"' + " ".join(rng.choice(['0','1']) for _ in range(rng.randint(4,16))) + '"'  # Not implemented in grammar yet
]

def _struct_op_factory(
        *,
        use_target: bool,
        min_length: int,
        max_examples: int,
        use_tree_metrics: bool,
    ) -> MutationOp:
    """
    Mutation operator that wraps an existing playable pattern inside a Tidal
    ``struct`` expression, which applies a boolean mask to control timing.

    This implementation works **purely at the tree level**:

      - It constructs the ``cp_mask_playable`` subtree directly using ``TreeNode``
        instances, matching the canonical shape produced by parsing expressions
        such as ``struct (\"t f\") (s(\"bd\"))`` with Lark.
      - The inner pattern is the existing ``PatternTree.root`` (no additional
        prefix transforms or textual round-trips).

    The resulting root has the form::

        control__cp_mask_playable
          STRUCT \"struct\"
          LPAR \"(\"
          control__pattern_bool__bool_literal
            control__pattern_bool__BOOL \"t f ...\"
          RPAR \")\"
          LPAR \"(\"
          <original-playable-root>
          RPAR \")\"
    """

    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # 1. Generate mask string (already quoted, e.g. "\"t f t f\"").
        mask_str = rng.choice(MASK_GENERATORS)(rng)

        # 2. Build the pattern_bool subtree for the mask:
        #       control__pattern_bool__bool_literal
        #         control__pattern_bool__BOOL: "<mask_str>"
        mask_node = TreeNode(
            op="control__pattern_bool__bool_literal",
            children=[
                TreeNode(op="control__pattern_bool__BOOL", value=mask_str),
            ],
        )

        # 3. Use the existing tree root as the playable term.
        #    Grammar (control.lark):
        #        cp_mask_playable: ("mask" | "struct" | "substruct")
        #                          "(" pattern_bool ")" "(" cp_playable_term ")"
        #    In practice, `PatternTree.root` is already one of the cp_playable_term
        #    variants (e.g. control__cp_sound_atom, control__cp_jux_playable, ...),
        #    so we can embed it directly.
        inner_playable = tree.root

        # 4. Build the cp_mask_playable root node that wraps the existing pattern.
        new_root = TreeNode(
            op="control__cp_mask_playable",
            children=[
                TreeNode(op="STRUCT", value="struct"),
                TreeNode(op="LPAR", value="("),
                mask_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                inner_playable,
                TreeNode(op="RPAR", value=")"),
            ],
        )

        return PatternTree(root=new_root)

    return op


def _overlay_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """
    Factory for an overlay-based mutation operator.

    This operator wraps the existing playable pattern and a freshly generated
    playable pattern in an ``overlay`` combinator, constructed **purely at the
    tree level**.  It builds the canonical `cp_playable_term` shape which, when
    parsed from text like::

        overlay (p1) (p2)

    yields a `PatternTree` of the form:

        control__cp_playable_term
          control__cp_binary_named
            OVERLAY \"overlay\"
          <left-playable>
          <right-playable>
    """

    # The config knobs are currently unused but kept for a consistent interface
    # and future experimentation (e.g. using targeted generation for the new
    # branch).
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Existing playable branch is the current root subtree.
        left_branch = tree.root

        # Generate a fresh playable pattern for the second branch.
        new_branch_tree = generate_expressions(1)[0]
        right_branch = new_branch_tree.root

        # Randomise argument order so we sometimes overlay base over new, and
        # sometimes new over base.
        if rng.random() < 0.5:
            first, second = left_branch, right_branch
        else:
            first, second = right_branch, left_branch

        # Build the cp_binary_named head: OVERLAY token under control__cp_binary_named.
        overlay_head = TreeNode(
            op="control__cp_binary_named",
            children=[TreeNode(op="OVERLAY", value="overlay")],
        )

        # Build the cp_playable_term root that applies overlay to the two branches.
        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[overlay_head, first, second],
        )

        return PatternTree(root=new_root)

    return op


def _append_op_factory(
    *, 
    use_target: bool = False, 
    min_length: int = 10, 
    max_examples: int = 500, 
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that creates a new pattern by appending a randomly
    generated pattern using the ``append`` / ``fastAppend`` combinators.

    This tree-level implementation mirrors the canonical parse shape for
    expressions like::

        append (p1) (p2)
        fastAppend (p1) (p2)

    which Lark parses into a ``PatternTree`` of the form:

        control__cp_playable_term
          control__cp_binary_named
            APPEND | FASTAPPEND
          <left-playable>
          <right-playable>

    We keep the previous semantics:
      - combinator is randomly chosen between ``append`` and ``fastAppend``,
      - argument order is randomized, so either the base or the new branch
        can appear on the left.

    Produces patterns like:
        append (basePattern) (newPattern)
        fastAppend (newPattern) (basePattern)
    """

    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Existing playable branch is the current root subtree.
        base_branch = tree.root

        # Generate 1–3-depth new branch as a fresh playable pattern.
        new_branch_tree = generate_expressions(rng.randint(1, 3))[0]
        new_branch_branch = new_branch_tree.root

        # Choose combinator: 'append' or 'fastAppend'.
        combinator = "append" if rng.random() < 0.5 else "fastAppend"

        # Randomize argument order: sometimes base on the left, sometimes right.
        if rng.random() < 0.5:
            left, right = base_branch, new_branch_branch
        else:
            left, right = new_branch_branch, base_branch

        # Build the cp_binary_named head with the appropriate token.
        if combinator == "append":
            head_token = TreeNode(op="APPEND", value="append")
        else:  # "fastAppend"
            head_token = TreeNode(op="FASTAPPEND", value="fastAppend")

        binary_head = TreeNode(
            op="control__cp_binary_named",
            children=[head_token],
        )

        # Build the cp_playable_term root that applies the combinator.
        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[binary_head, left, right],
        )

        return PatternTree(root=new_root)

    return op

# Inner transformations that can be applied within the "euclid" operator
EUCLID_TRANSFORMS = [
    "",          # No transformation
    "rev",     # Reverses the pattern in time
    "fast 2",  # Plays the pattern twice as fast
    "slow 2",  # Plays the pattern at half speed
    "iter 2",  # Iterates pattern twice within the same cycle
]

def _euclid_op_factory(
    *, 
    use_target: bool = False, 
    min_length: int = 10, 
    max_examples: int = 500, 
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that wraps an existing pattern inside a Tidal ``euclid``
    expression.

    This tree-level implementation mirrors the canonical parse shape for
    expressions like::

        euclid (pulses) (steps) (p)
        rev (euclid (pulses) (steps) (p))
        fast 2 (euclid (pulses) (steps) (p))

    Produces patterns like:
        euclid 5 16 (basePattern)
        rev $ (euclid 3 8 (basePattern))
    """
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Existing playable branch is the current root subtree.
        base_branch = tree.root

        # Choose pulses and steps
        step_choices = [8, 12, 16, 24, 32]
        steps = rng.choice(step_choices)
        pulses = rng.randint(1, steps)

        # Choose optional outer transformation
        transform = rng.choice(EUCLID_TRANSFORMS)

        # Build Pattern Int literal nodes for pulses and steps, matching the
        # structure produced by parsing e.g. `euclid (3) (8) (s("bd"))`:
        #
        #   control__pattern_int__int_literal
        #     control__pattern_int__INT "3"
        pulses_node = TreeNode(
            op="control__pattern_int__int_literal",
            children=[
                TreeNode(op="control__pattern_int__INT", value=str(pulses)),
            ],
        )
        steps_node = TreeNode(
            op="control__pattern_int__int_literal",
            children=[
                TreeNode(op="control__pattern_int__INT", value=str(steps)),
            ],
        )

        # Build the cp_euclid_playable subtree.
        euclid_node = TreeNode(
            op="control__cp_euclid_playable",
            children=[
                TreeNode(op="EUCLID", value="euclid"),
                TreeNode(op="LPAR", value="("),
                pulses_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                steps_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                base_branch,
                TreeNode(op="RPAR", value=")"),
            ],
        )

        # If no transform selected, the euclid node is already a playable term.
        if transform == "":
            return PatternTree(root=euclid_node)

        # Otherwise, wrap the euclid subtree in a prefix_cp-based cp_playable_term.
        prefix_children: list[TreeNode]

        if transform == "rev":
            # control__prefix_cp (REV)
            prefix_children = [TreeNode(op="REV", value="rev")]
        elif transform == "fast 2":
            # control__prefix_cp (FAST, control__pattern_time__INT "2")
            prefix_children = [
                TreeNode(op="FAST", value="fast"),
                TreeNode(op="control__pattern_time__INT", value="2"),
            ]
        elif transform == "slow 2":
            prefix_children = [
                TreeNode(op="SLOW", value="slow"),
                TreeNode(op="control__pattern_time__INT", value="2"),
            ]
        elif transform == "iter 2":
            prefix_children = [
                TreeNode(op="ITER", value="iter"),
                TreeNode(
                    op="control__pattern_int__int_literal",
                    children=[
                        TreeNode(op="control__pattern_int__INT", value="2"),
                    ],
                ),
            ]
        else:
            # Fallback: if an unexpected transform string appears, ignore it.
            return PatternTree(root=euclid_node)

        prefix_node = TreeNode(
            op="control__prefix_cp",
            children=prefix_children,
        )

        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[prefix_node, euclid_node],
        )

        return PatternTree(root=new_root)

    return op

def _scale_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a scale-based mutation operator that operates at tree level.
    
    Constructs patterns like:
        basePattern # n(scale "major" "0") # s("bd")
        
    The tree structure follows the left-associative infix chain:
        control_pattern
          <base_playable>
          control__cp_infix_op (OP_HASH)
          control__cp_note_atom (n(scale ...))
          control__cp_infix_op (OP_HASH)
          control__cp_sound_atom (s(...))
    """
    
    SCALE_NAMES = _SCALE_NAME_POOL
    INT_PATTERNS = _SCALE_INT_PATTERN_POOL
    SOUNDS = _SOUND_POOL
    
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics
    
    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        base_branch = tree.root
        scale_name = rng.choice(SCALE_NAMES)
        int_pattern = rng.choice(INT_PATTERNS)
        sound = rng.choice(SOUNDS)
        
        # 1. Build the scale constructor: n(scale "scale_name" "int_pattern")
        scale_literal_node = TreeNode(
            op="control__pattern_note__pattern_string_scale__scale_literal",
            children=[
                TreeNode(
                    op="control__pattern_note__pattern_string_scale__SCALE_STRING",
                    value=f'"{scale_name}"',
                )
            ],
        )
        
        int_string_literal_node = TreeNode(
            op="control__pattern_note__pattern_int__int_string_literal",
            children=[
                TreeNode(
                    op="control__pattern_note__pattern_int__STRING",
                    value=f'"{int_pattern}"',
                )
            ],
        )
        
        scale_ctor_node = TreeNode(
            op="control__pattern_note__scale_ctor",
            children=[scale_literal_node, int_string_literal_node],
        )
        
        note_atom_node = TreeNode(
            op="control__cp_note_atom",
            children=[
                TreeNode(
                    op="control__note_to_cp",
                    children=[TreeNode(op="N", value="n")],
                ),
                scale_ctor_node,
            ],
        )
        
        # 2. Build the sound atom: s("sound")
        sound_atom_node = TreeNode(
            op="control__cp_sound_atom",
            children=[
                TreeNode(op="S", value="s"),
                TreeNode(op="LPAR", value="("),
                TreeNode(
                    op="control__pattern_string_sample__sample_literal",
                    children=[
                        TreeNode(
                            op="control__pattern_string_sample__SAMPLE_STRING",
                            value=f'"{sound}"',
                        )
                    ],
                ),
                TreeNode(op="RPAR", value=")"),
            ],
        )
        
        # 3. Build infix operators (OP_HASH)
        hash_op_1 = TreeNode(
            op="control__cp_infix_op",
            children=[TreeNode(op="control__OP_HASH", value="#")],
        )
        
        hash_op_2 = TreeNode(
            op="control__cp_infix_op",
            children=[TreeNode(op="control__OP_HASH", value="#")],
        )
        
        # 4. Build the control_pattern root with left-associative infix chain
        new_root = TreeNode(
            op="control_pattern",
            children=[
                base_branch,
                hash_op_1,
                note_atom_node,
                hash_op_2,
                sound_atom_node,
            ],
        )
        
        return PatternTree(root=new_root)
    
    return op

def _note_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a note-based mutation operator that operates at tree level.
    
    Creates ControlPatterns using n/note with simple note patterns.
    
    The tree structure follows the left-associative infix chain:
        control_pattern
          <base_playable>
          control__cp_infix_op (OP_HASH)
          control__cp_note_atom (n/note "...")
          [optionally: control__cp_infix_op (OP_HASH) + control__cp_sound_atom]
    
    Produces patterns like:
        basePattern # n "0"
        basePattern # note "0 7"
        basePattern # n "0" # s("bd")  [when base has no sound]
    """
    
    NOTE_FUNCTIONS = ["n", "note"]
    
    # Note patterns (as strings) - these are the degrees/semitones
    NOTE_PATTERNS = _NOTE_PATTERN_POOL
    
    # Sound patterns to combine with
    SOUNDS = _SOUND_POOL
    
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        base_branch = tree.root
        
        # Choose components
        note_func = rng.choice(NOTE_FUNCTIONS)
        note_pattern = rng.choice(NOTE_PATTERNS)
        sound = rng.choice(SOUNDS)
        
        # Detect if base pattern already has sound by checking root op type
        # Sound-producing ops: cp_sound_atom, or patterns that likely have sound
        has_sound = base_branch.op in [
            "control__cp_sound_atom",
            "control__cp_lists_playable",
            "control__cp_euclid_playable",
            "control__cp_mask_playable",
            "control__cp_jux_playable",
            "control__cp_slice_playable",
            "control__cp_chop_playable",
            "control__cp_striate_playable",
            "control__cp_timeops_playable",
            "control__cp_applied_playable",
            "control__cp_playable_term",
            "control_pattern",
        ]
        
        # 1. Build the note atom: n/note "note_pattern"
        if note_func == "n":
            note_func_token = TreeNode(op="N", value="n")
        else:  # "note"
            note_func_token = TreeNode(op="NOTE", value="note")
        
        note_atom_node = TreeNode(
            op="control__cp_note_atom",
            children=[
                TreeNode(
                    op="control__note_to_cp",
                    children=[note_func_token],
                ),
                TreeNode(op="control__STRING", value=f'"{note_pattern}"'),
            ],
        )
        
        # 2. Build infix operator (OP_HASH)
        hash_op_1 = TreeNode(
            op="control__cp_infix_op",
            children=[TreeNode(op="control__OP_HASH", value="#")],
        )
        
        if has_sound:
            # Only add note, no additional sound
            new_root = TreeNode(
                op="control_pattern",
                children=[
                    base_branch,
                    hash_op_1,
                    note_atom_node,
                ],
            )
        else:
            # Add both note and sound
            hash_op_2 = TreeNode(
                op="control__cp_infix_op",
                children=[TreeNode(op="control__OP_HASH", value="#")],
            )
            
            sound_atom_node = TreeNode(
                op="control__cp_sound_atom",
                children=[
                    TreeNode(op="S", value="s"),
                    TreeNode(op="LPAR", value="("),
                    TreeNode(
                        op="control__pattern_string_sample__sample_literal",
                        children=[
                            TreeNode(
                                op="control__pattern_string_sample__SAMPLE_STRING",
                                value=f'"{sound}"',
                            )
                        ],
                    ),
                    TreeNode(op="RPAR", value=")"),
                ],
            )
            
            new_root = TreeNode(
                op="control_pattern",
                children=[
                    base_branch,
                    hash_op_1,
                    note_atom_node,
                    hash_op_2,
                    sound_atom_node,
                ],
            )
        
        return PatternTree(root=new_root)
    
    return op


def _speed_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that applies a speed transformation (fast or slow) to the pattern.
    Operates at tree level by constructing the appropriate prefix_cp structure.

    The tree structure follows:
        control__cp_playable_term
          control__prefix_cp
            FAST/SLOW token
            control__pattern_time__INT or control__pattern_time__DOUBLE (factor)
          <base_playable_subtree>

    Produces patterns like:
        fast 2 (basePattern)
        slow 0.5 (basePattern)
    """
    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        base_branch = tree.root

        # Choose fast or slow
        op_name = rng.choice(["fast", "slow"])

        # Choose factor from sensible values
        factors = [0.5, 1.5, 2, 3]
        factor = rng.choice(factors)

        # Build the prefix_cp node with the appropriate token and factor
        if op_name == "fast":
            op_token = TreeNode(op="FAST", value="fast")
        else:  # "slow"
            op_token = TreeNode(op="SLOW", value="slow")

        # Determine if factor is int or float, and create appropriate node
        if isinstance(factor, int) or factor == int(factor):
            factor_node = TreeNode(
                op="control__pattern_time__INT",
                value=str(int(factor)),
            )
        else:
            factor_node = TreeNode(
                op="control__pattern_time__DOUBLE",
                value=str(factor),
            )

        prefix_node = TreeNode(
            op="control__prefix_cp",
            children=[op_token, factor_node],
        )

        # Build the cp_playable_term root that applies the speed transformation
        new_root = TreeNode(
            op="control__cp_playable_term",
            children=[prefix_node, base_branch],
        )

        return PatternTree(root=new_root)

    return op


def _striate_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that applies striate to create a stutter/layering effect.
    Operates at tree level by constructing the appropriate cp_striate_playable structure.

    The tree structure follows:
        control__cp_striate_playable
          STRIATE token
          LPAR
          control__pattern_int__int_literal (n value)
          RPAR
          LPAR
          <base_playable_subtree>
          RPAR

    Produces patterns like:
        striate(3)(basePattern)
        striate(4)(basePattern)
    """
    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        base_branch = tree.root

        # Choose n from 2 to 6
        n_values = [2, 3, 4, 5, 6]
        n = rng.choice(n_values)

        # Build the int parameter node
        n_node = TreeNode(
            op="control__pattern_int__int_literal",
            children=[
                TreeNode(op="control__pattern_int__INT", value=str(n))
            ],
        )

        # Build the cp_striate_playable root
        new_root = TreeNode(
            op="control__cp_striate_playable",
            children=[
                TreeNode(op="STRIATE", value="striate"),
                TreeNode(op="LPAR", value="("),
                n_node,
                TreeNode(op="RPAR", value=")"),
                TreeNode(op="LPAR", value="("),
                base_branch,
                TreeNode(op="RPAR", value=")"),
            ],
        )

        return PatternTree(root=new_root)

    return op


def _clone_treenode(node: TreeNode) -> TreeNode:
    """Recursively clone a TreeNode subtree.

    This helper is used by mutation operators that want to avoid mutating
    the input PatternTree in-place.
    """
    return TreeNode(
        op=node.op,
        children=[_clone_treenode(child) for child in node.children],
        value=node.value,
    )


def _terminal_substitution_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
) -> MutationOp:
    """
    Mutation operator that randomly substitutes terminal musical values
    (sounds, note patterns, scale names and scale degree patterns) while
    preserving the tree structure.

    Each candidate terminal is mutated independently with a fixed probability.
    """
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    # Per-node mutation probabilities
    SOUND_PROB = 0.5
    NOTE_PROB = 0.5
    SCALE_PROB = 0.5

    def _maybe_substitute(node: TreeNode, rng: random.Random) -> None:
        op = node.op

        # Helper to pick a new quoted value from a pool, ideally different
        def _choose_new_quoted(current: Any, pool: list[str]) -> str:
            if not isinstance(current, str):
                inner_current = None
            elif len(current) >= 2 and current[0] == '"' and current[-1] == '"':
                inner_current = current[1:-1]
            else:
                inner_current = current

            if len(pool) > 1 and inner_current in pool:
                choices = [v for v in pool if v != inner_current]
            else:
                choices = pool

            new_inner = rng.choice(choices)
            return f'"{new_inner}"'

        # Sounds: control__pattern_string_sample__SAMPLE_STRING
        if op == "control__pattern_string_sample__SAMPLE_STRING":
            if rng.random() < SOUND_PROB:
                node.value = _choose_new_quoted(node.value, _SOUND_POOL)
            return

        # Note patterns: control__STRING (used under cp_note_atom)
        if op == "control__STRING":
            if rng.random() < NOTE_PROB:
                node.value = _choose_new_quoted(node.value, _NOTE_PATTERN_POOL)
            return

        # Scale names: control__pattern_note__pattern_string_scale__SCALE_STRING
        if op == "control__pattern_note__pattern_string_scale__SCALE_STRING":
            if rng.random() < SCALE_PROB:
                node.value = _choose_new_quoted(node.value, _SCALE_NAME_POOL)
            return

        # Scale degree patterns: control__pattern_note__pattern_int__STRING
        if op == "control__pattern_note__pattern_int__STRING":
            if rng.random() < SCALE_PROB:
                node.value = _choose_new_quoted(node.value, _SCALE_INT_PATTERN_POOL)
            return

    def _walk(node: TreeNode, rng: random.Random) -> None:
        _maybe_substitute(node, rng)
        for child in node.children:
            _walk(child, rng)

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Work on a cloned tree to avoid mutating the input in-place
        new_root = _clone_treenode(tree.root)
        _walk(new_root, rng)
        return PatternTree(root=new_root)

    return op


_MUTATION_OPERATOR_FACTORIES: Mapping[str, Callable[..., MutationOp]] = {
    # "subtree_replace": _subtree_replace_op_factory,
    # "stack_wrap": _stack_wrap_op_factory,
    # "struct": _struct_op_factory,
    # "overlay_wrap": _overlay_wrap_op_factory,
    # "append": _append_op_factory,
    # "euclid": _euclid_op_factory,
    # "scale_wrap": _scale_wrap_op_factory,
    # "note_wrap": _note_wrap_op_factory,
    # "speed": _speed_op_factory,
    # "striate": _striate_op_factory,
    "terminal_substitution": _terminal_substitution_op_factory,
}

def mutate_pattern_tree(
    tree: PatternTree,
    *,
    mutation_kinds: Sequence[str] = None,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
    rng: Optional[random.Random] = None,
) -> PatternTree:
    """Apply one of several mutation operators to ``tree`` and return the result.

    Parameters
    ----------
    tree:
        The input :class:`PatternTree` to mutate.
    mutation_kinds:
        A non-empty sequence of mutation operator names to choose from,
        e.g. ``(\"subtree_replace\", \"stack_wrap\")``.
    use_target, min_length, max_examples, use_tree_metrics:
        Configuration knobs passed through to operators that make use of the
        Hypothesis-based generation helpers.
    rng:
        Optional :class:`random.Random` instance to control randomness.  If
        omitted, the module-level :mod:`random` is used.
    """
    if rng is None:
        rng = random

    if not mutation_kinds:
        mutation_kinds = list(_MUTATION_OPERATOR_FACTORIES.keys())

    # Instantiate operator implementations with the given configuration.
    ops: List[MutationOp] = []
    for name in mutation_kinds:
        factory = _MUTATION_OPERATOR_FACTORIES.get(name)
        if factory is None:
            raise ValueError(f"Unknown mutation operator {name!r}")
        ops.append(
            factory(
                use_target=use_target,
                min_length=min_length,
                max_examples=max_examples,
                use_tree_metrics=use_tree_metrics,
            )
        )

    op = rng.choice(ops)
    return op(tree, rng)

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


def generate_expressions_targeted(
    n: int = 10,
    *,
    min_length: int = 30,
    max_examples: int = 1000,
    database: Any | None = None,
    use_tree_metrics: bool = True,
) -> List[PatternTree]:
    """Generate up to ``n`` complex patterns using Hypothesis' targeted search.

    Compared to :func:`generate_expressions`, this function uses a dedicated
    :func:`target`-driven search that biases the Hypothesis engine towards
    longer and structurally richer control patterns.  It is primarily intended
    for exploration and seeding of genetic algorithms, where diversity and
    complexity are more important than simplicity or shrinking behaviour.

    Parameters
    ----------
    n:
        Maximum number of patterns to return.
    min_length:
        Minimal allowed string length for a pattern to be considered
        ``interesting`` and collected.
    max_examples:
        Upper bound on the number of examples Hypothesis will explore while
        searching for high-scoring patterns.  Larger values increase runtime
        but typically yield more and more complex patterns.
    database:
        Optional Hypothesis example database.  The default ``None`` disables
        persistent storage, which helps avoid cross-run bias towards previously
        seen examples.
    use_tree_metrics:
        If ``True``, include tree depth and size as additional metrics for
        :func:`target`, in addition to raw string length.
    """
    pattern_strings = _collect_targeted_patterns(
        n,
        min_length=min_length,
        max_examples=max_examples,
        database=database,
        use_tree_metrics=use_tree_metrics,
    )

    results: List[PatternTree] = []
    for s in pattern_strings:
        try:
            parsed = parse_control_pattern(s)
        except Exception as e:
            print(f"Error parsing targeted pattern {s!r}: {e}")
            continue
        results.append(PatternTree.from_lark_tree(parsed))

    return results
