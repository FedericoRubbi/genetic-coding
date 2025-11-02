"""
Minimal example of pattern evolution using structural fitness.
Shows basic pattern generation and evolution with audio playback.
"""

import os
from pathlib import Path

# --- Internal imports, updated for new package layout ---
from genetic_music.genome.genome import Genome
from genetic_music.genome.population import evolve_population
from genetic_music.codegen.to_tidal import to_tidal
from genetic_music.backend.backend import Backend


def structural_fitness(genome: Genome) -> float:
    """Simple fitness function based on pattern structure."""
    tree = genome.pattern_tree

    depth = tree.depth()
    size = tree.size()

    ops, sounds = set(), set()

    def collect(node):
        ops.add(node.op)
        if node.op == "sound" and node.value:
            sounds.add(node.value)
        for child in node.children:
            collect(child)

    collect(tree)

    # Normalized scores
    depth_score = min(depth / 5, 1.0)
    variety_score = len(ops) / 10
    sound_score = len(sounds) / 4

    return 0.4 * depth_score + 0.3 * variety_score + 0.3 * sound_score


def main():
    # -------------------------------------------------------------------------
    # 1. Initialize backend for audio playback
    # -------------------------------------------------------------------------
    BOOT_TIDAL = os.path.expanduser(
        "/Users/federicorubbi/.cabal/share/aarch64-osx-ghc-9.12.2-ea3d/tidal-1.10.1/BootTidal.hs"
    )
    if not os.path.exists(BOOT_TIDAL):
        print("Please set the correct path to your BootTidal.hs file!")
        return

    backend = Backend(
        boot_tidal_path=BOOT_TIDAL,
        orbit=8,    # SuperDirt orbit to render on
        stream=12   # dedicated Tidal stream (d12)
    )

    # -------------------------------------------------------------------------
    # 2. Output directory
    # -------------------------------------------------------------------------
    output_dir = Path("data/outputs/minimal_evolution")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 3. Initial population
    # -------------------------------------------------------------------------
    pop_size = 10
    population = [Genome.random(pattern_depth=5) for _ in range(pop_size)]

    print("\nInitial Population:")
    print("=" * 50)
    for i, genome in enumerate(population):
        pattern = to_tidal(genome.pattern_tree)
        print(f"\nIndividual {i}:")
        print(f"Tree: {genome.pattern_tree}")
        print(f"Pattern: {pattern}")

    # -------------------------------------------------------------------------
    # 4. Evolution
    # -------------------------------------------------------------------------
    evolved = evolve_population(
        population=population,
        fitness_func=structural_fitness,
        mutation_rate=0.2,
        elitism=2,
    )

    # -------------------------------------------------------------------------
    # 5. Show and play best pattern
    # -------------------------------------------------------------------------
    best = max(evolved, key=lambda g: g.fitness)
    pattern = to_tidal(best.pattern_tree)

    print("\nBest Evolved Pattern:")
    print("=" * 50)
    print(f"Fitness: {best.fitness:.4f}")
    print(f"Tree: {best.pattern_tree}")
    print(f"Pattern: {pattern}")

    output_path = output_dir / "best_pattern.wav"
    print(f"\nPlaying and saving best pattern to: {output_path}")

    backend.play_tidal_code(
        rhs_pattern_expr=pattern,
        duration=8.0,
        output_path=output_path,
        playback_after=False,
    )

    backend.close()


if __name__ == "__main__":
    main()