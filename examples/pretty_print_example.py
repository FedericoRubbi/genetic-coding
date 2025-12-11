"""Example demonstrating the tree pretty-printing utilities.

This script shows how to visualize TidalCycles expression trees using the
pretty_print functions.
"""

from genetic_music.tree.pattern_tree import PatternTree


from genetic_music.generator import generate_expressions
from genetic_music.tree import (
    pretty_print,
    print_tree,
    tree_summary,
    print_tree_with_summary,
)
from genetic_music.tree.node import TreeNode
from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.genome.genome import Genome


def example_simple_manual_tree():
    """Example with a manually constructed tree."""
    print("=" * 70)
    print("Example 1: Simple Manual Tree")
    print("=" * 70)

    # Create a simple tree manually
    tree = TreeNode(
        op="control_pattern",
        children=[
            TreeNode(op="note", value="c"),
            TreeNode(op="note", value="e"),
            TreeNode(op="note", value="g"),
        ],
    )

    print("\nManually constructed tree:\n")
    print_tree_with_summary(tree)
    print()


def example_complex_manual_tree():
    """Example with a more complex manual tree."""
    print("=" * 70)
    print("Example 2: Complex Nested Tree")
    print("=" * 70)

    # Create a more complex nested tree
    tree = TreeNode(
        op="control_pattern",
        children=[
            TreeNode(
                op="fast",
                children=[
                    TreeNode(op="speed", value="2"),
                    TreeNode(
                        op="sequence",
                        children=[
                            TreeNode(op="note", value="c"),
                            TreeNode(op="note", value="e"),
                            TreeNode(op="note", value="g"),
                        ],
                    ),
                ],
            ),
            TreeNode(op="sound", value="superpiano"),
        ],
    )

    print("\nComplex nested tree:\n")
    print_tree_with_summary(tree)
    print()


def example_compact_mode():
    """Example showing compact mode."""
    print("=" * 70)
    print("Example 3: Compact vs Standard Mode")
    print("=" * 70)

    tree = TreeNode(
        op="operation",
        children=[
            TreeNode(op="param1", value="value1"),
            TreeNode(
                op="nested",
                children=[
                    TreeNode(op="param2", value="value2"),
                    TreeNode(op="param3", value="value3"),
                ],
            ),
            TreeNode(op="param4", value="value4"),
        ],
    )

    print("\nStandard view:")
    print_tree(tree, show_types=True, compact=False)

    print("\nCompact view:")
    print_tree(tree, show_types=True, compact=True)
    print()


def example_generated_patterns():
    """Example with randomly generated patterns."""
    print("=" * 70)
    print("Example 4: Generated TidalCycles Patterns")
    print("=" * 70)

    # Generate a few random patterns
    print("\nGenerating 3 random TidalCycles patterns...\n")
    patterns = generate_expressions(1)

    for i, tree in enumerate[PatternTree](patterns, 1):
        print(f"\n--- Generated Pattern {i} ---")
        print("Pattern: ", to_tidal(tree))
        print(tree_summary(tree))
        print("\nTree structure:")
        print_tree(tree.root, compact=False)
        print()

    # Mutate pattern
    genome = Genome(pattern_tree=patterns[0])
    mutated_genome = genome.mutate()
    print(f"\n--- Mutated Pattern ---")
    print("Pattern: ", to_tidal(mutated_genome.pattern_tree))
    print(tree_summary(mutated_genome.pattern_tree))
    print("\nTree structure:")
    print_tree(mutated_genome.pattern_tree.root, compact=False)
    print()


def example_without_types():
    """Example showing tree structure without type annotations."""
    print("=" * 70)
    print("Example 5: With/Without Type Annotations")
    print("=" * 70)

    tree = TreeNode(
        op="pattern",
        children=[
            TreeNode(op="note", value="c"),
            TreeNode(op="note", value="d"),
            TreeNode(op="note", value="e"),
        ],
    )

    print("\nWith types (default):")
    print_tree(tree, show_types=True)

    print("\nWithout types (values only):")
    print_tree(tree, show_types=False)
    print()


def example_deep_tree():
    """Example with a deep tree structure."""
    print("=" * 70)
    print("Example 6: Deep Tree Structure")
    print("=" * 70)

    # Create a deep tree (4 levels)
    tree = TreeNode(
        op="level0",
        children=[
            TreeNode(
                op="level1_a",
                children=[
                    TreeNode(
                        op="level2_a",
                        children=[
                            TreeNode(op="level3_a", value="leaf_a"),
                            TreeNode(op="level3_b", value="leaf_b"),
                        ],
                    ),
                    TreeNode(
                        op="level2_b",
                        children=[
                            TreeNode(op="level3_c", value="leaf_c"),
                        ],
                    ),
                ],
            ),
            TreeNode(
                op="level1_b",
                children=[
                    TreeNode(op="level2_c", value="leaf_d"),
                ],
            ),
        ],
    )

    print("\nDeep tree structure:\n")
    print_tree_with_summary(tree)
    print()


def example_using_pretty_print_string():
    """Example using pretty_print to get a string."""
    print("=" * 70)
    print("Example 7: Using pretty_print() to Get String")
    print("=" * 70)

    tree = TreeNode(
        op="root",
        children=[
            TreeNode(op="child1", value="A"),
            TreeNode(op="child2", value="B"),
        ],
    )

    # Get the pretty-printed string
    tree_str = pretty_print(tree)

    print("\nTree as string (can be stored or processed):")
    print(tree_str)

    print("\nString length:", len(tree_str))
    print("Number of lines:", len(tree_str.split("\n")))
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "TidalCycles Tree Pretty Print Examples" + " " * 14 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # example_simple_manual_tree()
    # example_complex_manual_tree()
    # example_compact_mode()
    # example_without_types()
    # example_deep_tree()
    # example_using_pretty_print_string()
    example_generated_patterns()

    print("=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nYou can now use these functions in your own code:")
    print("  - from genetic_music.tree import print_tree, pretty_print")
    print("  - print_tree(your_tree)")
    print("  - tree_str = pretty_print(your_tree)")


if __name__ == "__main__":
    main()
