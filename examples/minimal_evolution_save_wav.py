"""
Minimal example of pattern evolution using structural fitness.
Shows basic pattern generation and evolution with audio playback.
"""

import os
from pathlib import Path

# --- Internal imports, updated for new package layout ---
from genetic_music.genome.genome import Genome
from genetic_music.genome.population import evolve_population
from genetic_music.generator import generate_expressions_mutational
from genetic_music.backend.backend import Backend
from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.fitness_evaluation.fitness_evaluation import get_fitness


def structural_fitness(genome: Genome) -> float:
    """Simple fitness function based on pattern structure."""
    tree = genome.pattern_tree

    depth = tree.depth()
    size = tree.size()

    ops, sounds = set(), set()

    def collect(node):
        # Track which grammar rules / token types appear.
        ops.add(node.op)
        # SAMPLE_STRING leaves encode concrete sample names such as "bd", "sn", etc.
        # In the PatternTree they appear with module‑qualified op names like
        # ``control__pattern_string_sample__SAMPLE_STRING`` and a quoted value.
        if "SAMPLE_STRING" in node.op and node.value:
            # Strip surrounding quotes for readability when counting unique sounds.
            sounds.add(node.value.strip('"'))
        for child in node.children:
            collect(child)

    # Start from the underlying root node to avoid treating PatternTree itself
    # as a node in the structural walk.
    collect(tree.root)

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
    
    # Load BootTidal path from config
    from genetic_music.config import get_boot_tidal_path
    
    try:
        BOOT_TIDAL = get_boot_tidal_path()
        if not BOOT_TIDAL:
            print("ERROR: BootTidal.hs path not configured!")
            print("Please create a config.yaml file (see config.yaml.example) and set tidal.boot_file_path")
            return
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
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
    pop_size = 3
    expressions = generate_expressions_mutational(pop_size)
    population = [Genome(pattern_tree=expression) for expression in expressions]

    print("\nInitial Population:")
    print("=" * 50)
    for i, genome in enumerate(population):
        # if i != 0:
        #     continue
        print(f"\nIndividual {i}:")
        # print(f"Tree: {genome.pattern_tree}")
        print(f"Tidal code: {to_tidal(genome.pattern_tree)}")

    # -------------------------------------------------------------------------
    # 4. Evolution
    # -------------------------------------------------------------------------

    evolved = population
    for _ in range(3):
        evolved = evolve_population(
            population=evolved,
            fitness_func=get_fitness,
            mutation_rate=1,
            elitism=0,
        )

        best = max(evolved, key=lambda g: g.fitness)
        print(f"Evolved population size: {len(evolved)}")
        mutated_example = best.mutate(rate=1.0)
        print("\nMutated variant of best individual (sanity check):")
        print("-" * 50)
        print(f"Original Tidal: {to_tidal(best.pattern_tree)}")
        print(f"Mutated Tidal:  {to_tidal(mutated_example.pattern_tree)}")

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