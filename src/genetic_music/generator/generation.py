"""Utilities for generating and parsing control patterns with Lark.

This module exposes a small, tidy API:

- ``parse_control_pattern(text)`` -> Lark parse tree
- ``pattern_tree_from_string(text)`` -> :class:`PatternTree`
- ``generate_expressions(n)`` -> list of :class:`PatternTree` generated via
  a custom seed-then-mutate generator over the TidalCycles AST.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from lark import Lark, Token, Tree

from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.tree.node import TreeNode
from genetic_music.tree.pattern_tree import PatternTree

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

MutationOp = Callable[[PatternTree, random.Random], PatternTree]


# ---------------------------------------------------------------------------
# Tree helpers (used by crossover and some mutations)
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


def _truncate_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
) -> MutationOp:
    """
    Mutation operator that simplifies composite patterns by truncating
    overlay/append/stack-style combinators.

    It searches for:
      - Binary named combinators (overlay / append / slowAppend / fastAppend / interlace)
        represented as:
            control__cp_playable_term
              control__cp_binary_named(HEAD)
              <left_playable>
              <right_playable>
        and replaces the whole node with either the left or right branch.
      - List-based combinators (stack / cat / fastcat / slowcat), represented as:
            control__cp_lists_playable
              STACK/CAT token
              control__cp_list_playable([...playable/any children...])
        and replaces the whole node with one playable element from the list.

    Only a single combinator is truncated per mutation, chosen uniformly at random.
    """
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    # Token types for named binary combinators we want to truncate
    BINARY_HEAD_TOKENS = {
        "OVERLAY",
        "APPEND",
        "SLOWAPPEND",
        "FASTAPPEND",
        "INTERLACE",
    }

    # Ops that correspond to playable CP roots (from cp_playable_term alternatives)
    PLAYABLE_OPS = {
        "control__cp_playable_term",
        "control__cp_sound_atom",
        "control__cp_note_atom",
        "control__cp_applied_playable",
        "control__cp_jux_playable",
        "control__cp_slice_playable",
        "control__cp_chop_playable",
        "control__cp_mask_playable",
        "control__cp_striate_playable",
        "control__cp_euclid_playable",
        "control__cp_timeops_playable",
        "control__cp_lists_playable",
    }

    Candidate = tuple[str, TreeNode, Optional[TreeNode], Optional[int]]

    def _collect_candidates(root: TreeNode) -> list[Candidate]:
        candidates: list[Candidate] = []

        def _walk(node: TreeNode, parent: Optional[TreeNode], index_in_parent: Optional[int]) -> None:
            # Binary named combinators under cp_playable_term
            if node.op == "control__cp_playable_term" and len(node.children) >= 3:
                head = node.children[0]
                if head.op == "control__cp_binary_named" and head.children:
                    head_tok = head.children[0]
                    if head_tok.op in BINARY_HEAD_TOKENS:
                        # children[1] and children[2] are the two branches
                        candidates.append(("binary", node, parent, index_in_parent))

            # Stack/list combinators: cp_lists_playable(stack/cat/... [ ... ])
            if node.op == "control__cp_lists_playable" and len(node.children) >= 2:
                list_node = node.children[1]
                if list_node.op == "control__cp_list_playable" and list_node.children:
                    candidates.append(("list", node, parent, index_in_parent))

            for idx, child in enumerate(node.children):
                _walk(child, node, idx)

        _walk(root, None, None)
        return candidates

    def _truncate_once(root: TreeNode, rng: random.Random) -> TreeNode:
        candidates = _collect_candidates(root)
        if not candidates:
            return root

        kind, node, parent, index_in_parent = rng.choice(candidates)

        # Decide which subtree should replace the combinator node
        survivor: Optional[TreeNode] = None

        if kind == "binary":
            # Expect shape: [binary_head, left, right, ...]
            if len(node.children) >= 3:
                left = node.children[1]
                right = node.children[2]
                survivor = left if rng.random() < 0.5 else right

        elif kind == "list":
            # Expect shape: [STACK/CAT token, cp_list_playable]
            list_node = node.children[1]
            # Filter to playable children only, to preserve cp_playable_term invariants
            playable_children = [c for c in list_node.children if c.op in PLAYABLE_OPS]
            if playable_children:
                survivor = rng.choice(playable_children)

        # If something unexpected happened, leave the tree unchanged
        if survivor is None:
            return root

        # Replace in parent or at root
        if parent is None or index_in_parent is None:
            # Truncated node was the root
            return survivor

        parent.children[index_in_parent] = survivor
        return root

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Operate on a clone to avoid mutating the input tree
        new_root = _clone_treenode(tree.root)
        new_root = _truncate_once(new_root, rng)
        return PatternTree(root=new_root)

    return op


def _stack_enrich_op_factory(
    *,
    use_target: bool = False,
    min_length: int = 10,
    max_examples: int = 500,
    use_tree_metrics: bool = True,
) -> MutationOp:
    """
    Mutation operator that enriches existing stack/cat-style list combinators
    by appending additional randomly generated branches.

    It targets nodes of the form::

        control__cp_lists_playable
          STACK/CAT token
          control__cp_list_playable(<children...>)

    and appends 1–3 new playable subtrees to the ``control__cp_list_playable``
    children list, leaving the overall combinator and existing branches intact.
    """
    # Unused config parameters kept intentionally for future tuning
    del use_target, min_length, max_examples, use_tree_metrics

    def _collect_stack_nodes(root: TreeNode) -> list[tuple[TreeNode, TreeNode]]:
        """Return (lists_node, list_node) pairs for all cp_lists_playable nodes."""
        nodes: list[tuple[TreeNode, TreeNode]] = []

        def _walk(node: TreeNode) -> None:
            if node.op == "control__cp_lists_playable" and len(node.children) >= 2:
                list_node = node.children[1]
                if list_node.op == "control__cp_list_playable":
                    nodes.append((node, list_node))
            for child in node.children:
                _walk(child)

        _walk(root)
        return nodes

    def _enrich_once(root: TreeNode, rng: random.Random) -> TreeNode:
        candidates = _collect_stack_nodes(root)
        if not candidates:
            return root

        _, list_node = rng.choice(candidates)

        # Decide how many new branches to add
        n_new = rng.randint(1, 3)
        new_branch_trees = generate_expressions(n_new)

        for pt in new_branch_trees:
            # Append the playable subtree root directly to the list
            list_node.children.append(pt.root)

        return root

    def op(tree: PatternTree, rng: random.Random) -> PatternTree:
        # Operate on a clone to avoid mutating the input tree
        new_root = _clone_treenode(tree.root)
        new_root = _enrich_once(new_root, rng)
        return PatternTree(root=new_root)

    return op


_MUTATION_OPERATOR_FACTORIES: Mapping[str, Callable[..., MutationOp]] = {
    # "stack_wrap": _stack_wrap_op_factory,
    # "struct": _struct_op_factory,
    # "overlay_wrap": _overlay_wrap_op_factory,
    # "append": _append_op_factory,
    # "euclid": _euclid_op_factory,
    # "scale_wrap": _scale_wrap_op_factory,
    # "note_wrap": _note_wrap_op_factory,
    # "speed": _speed_op_factory,
    # "striate": _striate_op_factory,
    # "terminal_substitution": _terminal_substitution_op_factory,
    "truncate": _truncate_op_factory,
    # "stack_enrich": _stack_enrich_op_factory,
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


def _random_seed_pattern(rng: random.Random) -> PatternTree:
    """Generate a small, simple seed pattern as a :class:`PatternTree`.

    Seeds are intentionally tiny (single sounds, simple note patterns, or
    short stacks) and are later grown by applying tree-level mutation
    operators in :func:`generate_expressions_mutational`.
    """
    # Simple families of seed patterns
    seed_kind = rng.choice(["sound", "note", "stack"])

    if seed_kind == "sound":
        sound = rng.choice(_SOUND_POOL)
        code = f's("{sound}")'
    elif seed_kind == "note":
        sound = rng.choice(_SOUND_POOL)
        note_pattern = rng.choice(_NOTE_PATTERN_POOL)
        code = f's("{sound}") # n "{note_pattern}"'
    else:  # "stack"
        # 2–3 simple sound atoms stacked together
        k = rng.randint(2, 3)
        sounds = [rng.choice(_SOUND_POOL) for _ in range(k)]
        inner = ",".join(f's("{s}")' for s in sounds)
        code = f"stack[{inner}]"

    try:
        return pattern_tree_from_string(code)
    except Exception:
        # Fallback: if parsing fails for any reason, fall back to a very simple seed.
        return pattern_tree_from_string('s("bd")')


def generate_expressions(n: int = 10) -> List[PatternTree]:
    """Generate ``n`` random control patterns as :class:`PatternTree` objects.

    This is a convenience wrapper around :func:`generate_expressions_mutational`
    using its default configuration.
    """
    return generate_expressions_mutational(n=n)


def generate_expressions_mutational(
    n: int = 10,
    *,
    min_steps: int = 3,
    max_steps: int = 12,
    target_size: tuple[int, int] | None = None,
    target_depth: tuple[int, int] | None = None,
    rng: Optional[random.Random] = None,
) -> List[PatternTree]:
    """Generate ``n`` random patterns by seed-then-mutate over PatternTrees.

    This generator avoids direct Lark-based sampling in favour of:

      1. Sampling a small seed pattern (simple sound/note/stack).
      2. Applying a sequence of tree-level mutation operators to grow and
         enrich the pattern until the desired size/depth region is reached.

    It reuses the existing mutation operators defined in this module and
    therefore guarantees grammar-correct output as long as the operators do.
    """
    if rng is None:
        rng = random

    if target_size is None:
        target_size = (10, 120)
    if target_depth is None:
        target_depth = (3, 12)

    # Group mutation factories by their overall effect on structure.
    grow_factories: List[Callable[..., MutationOp]] = [
        _stack_wrap_op_factory,
        _overlay_wrap_op_factory,
        _append_op_factory,
        _scale_wrap_op_factory,
        _note_wrap_op_factory,
        _euclid_op_factory,
        _struct_op_factory,
        _striate_op_factory,
        _speed_op_factory,
        _stack_enrich_op_factory,
    ]
    value_factories: List[Callable[..., MutationOp]] = [
        _terminal_substitution_op_factory,
    ]
    shrink_factories: List[Callable[..., MutationOp]] = [
        _truncate_op_factory,
    ]

    results: List[PatternTree] = []

    while len(results) < n:
        tree = _random_seed_pattern(rng if isinstance(rng, random.Random) else random.Random())

        steps = rng.randint(min_steps, max_steps)
        for _ in range(steps):
            size = tree.size()
            depth = tree.depth()

            too_small = size < target_size[0] or depth < target_depth[0]
            too_big = size > target_size[1] or depth > target_depth[1]

            factories: List[Callable[..., MutationOp]]

            if too_big and shrink_factories:
                factories = shrink_factories
            elif too_small and grow_factories:
                factories = grow_factories
            else:
                # Within target band: mix growth, value-only tweaks, and occasional shrink.
                p = rng.random()
                if p < 0.5 and grow_factories:
                    factories = grow_factories
                elif p < 0.8 and value_factories:
                    factories = value_factories
                elif shrink_factories:
                    factories = shrink_factories
                else:
                    factories = grow_factories or value_factories or shrink_factories

            if not factories:
                break

            factory = rng.choice(factories)

            try:
                op = factory(
                    use_target=False,
                    min_length=10,
                    max_examples=500,
                    use_tree_metrics=True,
                )
                tree = op(tree, rng)
            except Exception as e:
                # If a mutation fails for any reason, stop mutating this individual
                # and keep the latest valid tree.
                print(f"Error during mutational generation step: {e}")
                break

        results.append(tree)

    return results
