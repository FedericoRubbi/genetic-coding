"""
Minimal example of pattern evolution using structural fitness.
Shows basic pattern generation and evolution with audio playback.
"""

import os
from pathlib import Path

# --- Internal imports, updated for new package layout ---
from genetic_music.genome.genome import Genome
from genetic_music.genome.population import evolve_population
from genetic_music.generator.generation import generate_expressions
from genetic_music.backend.backend import Backend
from genetic_music.codegen.tidal_codegen import to_tidal


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
    # 1. Initialize backend for audio playback and recording
    # -------------------------------------------------------------------------
    print(f"Current working directory: {Path.cwd()}")
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
    # 3. Initial population (PatternTree-based genomes)
    # -------------------------------------------------------------------------
    pop_size = 10
    expressions = generate_expressions(pop_size)
    population = [Genome(pattern_tree=expression) for expression in expressions]

    print("\nInitial Population:")
    print("=" * 50)
    for i, genome in enumerate(population):
        print(f"\nIndividual {i}:")
        print(f"Tree: {genome.pattern_tree}")

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
    # 5. Show best pattern and save a WAV file
    # -------------------------------------------------------------------------
    best = max(evolved, key=lambda g: g.fitness)

    print("\nBest Evolved Pattern:")
    print("=" * 50)
    print(f"Fitness: {best.fitness:.4f}")
    print(f"Tree: {best.pattern_tree}")
    pattern = to_tidal(best.pattern_tree)
    print(f"Pattern: {pattern}")

    output_path = output_dir / "best_pattern.wav"
    abs_output_path = output_path.resolve()
    print(f"\nRecording best pattern to: {abs_output_path}")

    recorded_path = backend.play_tidal_code(
        rhs_pattern_expr=pattern,
        duration=8.0,
        output_path=output_path,
        playback_after=False,
    )

    recorded_path = recorded_path.resolve()
    if recorded_path.exists():
        print(f"[minimal_evolution_save_wav] Backend reported output at path: {recorded_path}")
    else:
        print(f"[minimal_evolution_save_wav] Backend reported no output at path: {recorded_path}")

    backend.close()


if __name__ == "__main__":
    main()