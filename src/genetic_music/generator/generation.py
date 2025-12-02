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

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-'\"()"
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
        if not isinstance(s, str) or not s.strip():
            return

        if use_target:
            target(float(len(s)), label="subtree_length")

        if len(collected) >= n:
            return

        try:
            parsed = _MUTATION_PARSER.parse(s, start=rule_name)
            ptree = PatternTree.from_lark_tree(parsed)
        except Exception:
            return

        if use_target and use_tree_metrics:
            target(float(ptree.size()), label="subtree_size")
            target(float(ptree.depth()), label="subtree_depth")

        if len(s) >= min_length and len(collected) < n:
            collected.append(ptree.root)

    _explore()
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
        # Convert the existing pattern to Tidal code.
        base_code = to_tidal(tree)

        # Generate a fresh playable pattern for the second branch.
        new_branch_trees = generate_expressions(1)
        new_branch_code = to_tidal(new_branch_trees[0])

        # Build a stack expression: stack [base, new]
        stacked_code = f"stack [{base_code}, {new_branch_code}]"

        # Parse back into a PatternTree.
        return pattern_tree_from_string(stacked_code)

    return op

# Inner transformations that can be applied within the "struct" operator
STRUCT_INNERS = [
    "rev",          # Reverses the pattern in time
    "fast 2",       # Plays the pattern twice as fast
    "slow 2",       # Plays the pattern at half speed
    "iter 2",       # Iterates pattern twice within the same cycle
    "degradeBy 0.2" # Probabilistically drops 20% of the events
]

# Functions used to create valid "mask" patterns for the "struct" operator, that define when events are allowed to occur
MASK_GENERATORS = [
    # Boolean mask t(a,b): a pulses across b positions
    lambda rng: f"t({rng.randint(2,8)},{rng.choice([8,12,16])})",
    # Binary string mask (e.g: "1011001")
    lambda rng: '"' + "".join(rng.choice(['0','1']) for _ in range(rng.randint(4,16))) + '"'
]

def _struct_op_factory(
        *,
        use_target: bool,
        min_length: int,
        max_examples: int,
        use_tree_metrics: bool,
    ) -> MutationOp:
    """
    Mutation operator that wraps an existing pattern inside a Tidal "struct" expression, 
    which applies a mask to control timing. Optionally applies a transformation.

    Produces patterns like:
        struct ("0101") (basePattern)
        struct (t(3,8)) (rev (basePattern))
    """

    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Convert the existing pattern to Tidal code
        base = to_tidal(tree)

        # Choose inner transformation
        inner = rng.choice(STRUCT_INNERS)

        # Generate a valid mask
        mask = rng.choice(MASK_GENERATORS)(rng)

        # Struct expression with 50% chance of including inner transformation
        if rng.random() < 0.5:
            structured_code = f"struct ({mask}) ({inner} ({base}))"
        else:
            structured_code = f"struct ({mask}) ({base})"

        # Parse back into a PatternTree
        return pattern_tree_from_string(structured_code)

    return op


def append_op_factory(
    *, 
    use_target: bool = False, 
    min_length: int = 10, 
    max_examples: int = 500, 
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that creates a new pattern by appending a randomly generated pattern.
    Either "append" or "fastAppend" combinator is used (with randomized argument order), where:
        "append" combines two patterns sequentially.
        "fastAppend" combines two patterns by interleaving their events.

    Produces patterns like:
        append (basePattern) (newPattern)
        fastAppend (newPattern) (basePattern)
    """

    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Convert the existing pattern to Tidal code
        base_code = to_tidal(tree)

        # Generate 1–3-depth new branch
        new_branch_tree = generate_expressions(rng.randint(1, 3))[0]
        new_branch_code = to_tidal(new_branch_tree)

        # Choose combinator
        combinator = "append" if rng.random() < 0.5 else "fastAppend"

        # Randomize argument order
        if rng.random() < 0.5:
            appended_code = f"{combinator} ({base_code}) ({new_branch_code})"
        else:
            appended_code = f"{combinator} ({new_branch_code}) ({base_code})"

        # Parse back into a PatternTree
        return pattern_tree_from_string(appended_code)

    return op

# Inner transformations that can be applied within the "euclid" operator
EUCLID_TRANSFORMS = [
    "",          # No transformation
    "rev $",     # Reverses the pattern in time
    "fast 2 $",  # Plays the pattern twice as fast
    "slow 2 $",  # Plays the pattern at half speed
    "iter 2 $",  # Iterates pattern twice within the same cycle
]

def euclid_op_factory(
    *, 
    use_target: bool = False, 
    min_length: int = 10, 
    max_examples: int = 500, 
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that wraps an existing pattern inside a Tidal "euclid" expression.

    Produces patterns like:
        euclid 5 16 (basePattern)
        rev $ (euclid 3 8 (basePattern))
    """
    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Convert the existing pattern to Tidal code
        base_code = to_tidal(tree)

        # Choose pulses and steps
        step_choices = [8, 12, 16, 24, 32]
        steps = rng.choice(step_choices)
        pulses = rng.randint(1, steps)

        # Choose transformation
        transform = rng.choice(EUCLID_TRANSFORMS)

        # Build final euclid expression (if transform is empty, no transformation is applied)
        if transform == "":
            euclid_code = f"euclid {pulses} {steps} ({base_code})"
        else:
            euclid_code = f"{transform} (euclid {pulses} {steps} ({base_code}))"

        # Parse back into a PatternTree
        return pattern_tree_from_string(euclid_code)

    return op

def _scale_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a scale-based mutation operator."""
     
    SCALE_NAMES = ["major", "minor", "dorian", "ritusen"]
    INT_PATTERNS = ["0", "0 2 4", "0 .. 7"]
    SOUNDS = ["bd", "sn", "hh", "cp", "tabla", "arpy"]
    
    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        base_code = to_tidal(tree)
        scale_name = rng.choice(SCALE_NAMES)
        int_pattern = rng.choice(INT_PATTERNS)
        sound = rng.choice(SOUNDS)
        
        # Generate complete pattern with sound
        pattern_code = f'{base_code}#n(scale"{scale_name}""{int_pattern}")#s("{sound}")'
        
        return pattern_tree_from_string(pattern_code)
    
    return op

def _note_wrap_op_factory(
    *,
    use_target: bool,
    min_length: int,
    max_examples: int,
    use_tree_metrics: bool,
) -> MutationOp:
    """Factory for a note-based mutation operator.
    
    Creates ControlPatterns using n/note with simple note patterns.
    """
    
    NOTE_FUNCTIONS = ["n", "note"]
    
    # Note patterns (as strings) - these are the degrees/semitones
    NOTE_PATTERNS = [
        "0", "0 7", "0 4 7", "0 2 4 5 7 9 11", 
        "0 .. 11", "-12 .. 12", "24 36 48",
        "60", "60 64 67", "0.5", "1.5" 
    ]
    
    # Sound patterns to combine with
    SOUNDS = ["bd", "sn", "hh", "cp", "tabla", "arpy"]

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
       
        # Get the existing pattern
        base_code = to_tidal(tree)
        
        # Choose components
        note_func = rng.choice(NOTE_FUNCTIONS)
        note_pattern = rng.choice(NOTE_PATTERNS)
        sound = rng.choice(SOUNDS)
        
        # Check if base_code already has sound
        # Simple heuristic - if it contains 'sound' or 's ', assume it has sound
        has_sound = ('sound' in base_code) or ('s ' in base_code)
        
        if has_sound:
            # Overlay note pattern on existing sound
            pattern_code = f'{base_code}#{note_func}"{note_pattern}"'
        else:
            # Add both note and sound to base pattern
            pattern_code = f'{base_code}#{note_func}"{note_pattern}"#s("{sound}")'
        
        return pattern_tree_from_string(pattern_code)
    
    return op


def speed_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that applies a speed transformation (fast or slow) to the pattern.

    Produces patterns like:
        fast 2 $ (basePattern)
        slow 0.5 $ (basePattern)
    """
    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Convert the existing pattern to Tidal code
        base_code = to_tidal(tree)

        # Choose fast or slow
        op_name = rng.choice(["fast", "slow"])

        # Choose factor from sensible values
        factors = [0.5, 1.5, 2, 3]
        factor = rng.choice(factors)

        # Build speed expression
        speed_code = f"{op_name} {factor} $ ({base_code})"

        # Parse back into a PatternTree
        return pattern_tree_from_string(speed_code)

    return op


def striate_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True
) -> MutationOp:
    """
    Mutation operator that applies striate to create a stutter/layering effect.

    Produces patterns like:
        striate 3 $ (basePattern)
    """
    # Unused config parameters kept intentionally
    del use_target, min_length, max_examples, use_tree_metrics

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Convert the existing pattern to Tidal code
        base_code = to_tidal(tree)

        # Choose n from 2 to 6
        n_values = [2, 3, 4, 5, 6]
        n = rng.choice(n_values)

        # Build striate expression
        striate_code = f"striate {n} $ ({base_code})"

        # Parse back into a PatternTree
        return pattern_tree_from_string(striate_code)

    return op


_MUTATION_OPERATOR_FACTORIES: Mapping[str, Callable[..., MutationOp]] = {
    "subtree_replace": _subtree_replace_op_factory,
    "stack_wrap": _stack_wrap_op_factory,
    "struct": _struct_op_factory,
    "append": append_op_factory,
    "euclid": euclid_op_factory,
    "scale_wrap": _scale_wrap_op_factory,
    "note_wrap": _note_wrap_op_factory,
    "speed": speed_op_factory,
    "striate": striate_op_factory,
}

def mutate_pattern_tree(
    tree: PatternTree,
    *,
    mutation_kinds: Sequence[str] = ("subtree_replace",),
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
        mutation_kinds = ("subtree_replace",)

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
