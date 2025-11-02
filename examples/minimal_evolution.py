"""
Minimal example of pattern evolution using structural fitness.
Shows basic pattern generation and evolution with audio playback.
"""

import os
from pathlib import Path
from genetic_music import Genome, evolve_population
from genetic_music.codegen import to_tidal
from genetic_music.backend import Backend


def structural_fitness(genome: Genome) -> float:
    """
    Simple fitness function based on pattern structure.
    Rewards:
    - Tree depth (complexity)
    - Variety of operators
    - Number of different sounds
    """
    tree = genome.pattern_tree
    
    # Get tree stats
    depth = tree.depth()
    size = tree.size()
    
    # Count unique operators and sounds
    ops = set()
    sounds = set()
    
    def collect_stats(node):
        ops.add(node.op)
        if node.op == 'sound' and node.value:
            sounds.add(node.value)
        for child in node.children:
            collect_stats(child)
    
    collect_stats(tree)
    
    # Compute normalized scores
    depth_score = min(depth / 5, 1.0)  # Max depth of 5
    variety_score = len(ops) / 10  # Normalize by reasonable max
    sound_score = len(sounds) / 4  # Reward using up to 4 different sounds
    
    # Combined score with weights
    return 0.4 * depth_score + 0.3 * variety_score + 0.3 * sound_score


def main():
    # Initialize backend for audio playback
    # You need to set the path to your BootTidal.hs file
    BOOT_TIDAL = os.path.expanduser("/Users/federicorubbi/.cabal/share/aarch64-osx-ghc-9.12.2-ea3d/tidal-1.10.1/BootTidal.hs")
    if not os.path.exists(BOOT_TIDAL):
        print("Please set the correct path to your BootTidal.hs file!")
        return

    backend = Backend(
        boot_tidal_path=BOOT_TIDAL,
        orbit=8,    # SuperDirt orbit to render on
        stream=12   # dedicated Tidal stream (d12) for our patterns
    )

    output_dir = os.path.abspath('data/outputs/minimal_evolution')
    os.makedirs(output_dir, exist_ok=True)

    # Create small initial population
    pop_size = 10
    population = [Genome.random(pattern_depth=3) for _ in range(pop_size)]
    
    # Show initial population
    print("\nInitial Population:")
    print("=" * 50)
    for i, genome in enumerate(population):
        pattern = to_tidal(genome.pattern_tree)
        print(f"\nIndividual {i}:")
        print(f"Tree: {genome.pattern_tree}")
        print(f"Pattern: {pattern}")
    
    # Evolve for a few generations
    generations = 5
    evolved = evolve_population(
        population=population,
        fitness_fn=structural_fitness,
        generations=generations,
        crossover_rate=0.8,
        mutation_rate=0.2,
        elite_size=2,
        selection_method='tournament'
    )
    
    # Show best result
    print("\nBest Evolved Pattern:")
    print("=" * 50)
    best = max(evolved, key=lambda g: g.fitness)
    print(f"\nFitness: {best.fitness:.4f}")
    print(f"Tree: {best.pattern_tree}")
    pattern = to_tidal(best.pattern_tree)
    print(f"Pattern: {pattern}")
    
    # Play the best pattern and save it
    output_path = os.path.join(output_dir, f"best_pattern.wav")
    print(f"\nPlaying and saving best pattern to: {output_path}")
    backend.play_tidal_code(
        rhs_pattern_expr=pattern,
        duration=8.0,
        output_path=Path(output_path),
        playback_after=True  # This will play back the recording after it's done
    )
    
    # Clean up
    backend.close()


if __name__ == "__main__":
    main()