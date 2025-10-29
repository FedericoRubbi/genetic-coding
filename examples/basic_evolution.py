"""
Basic example of genetic music evolution.

This script demonstrates the basic workflow:
1. Create a random population
2. Evaluate fitness
3. Evolve for several generations
4. Save the best individual
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genetic_music import Genome, Backend, evolve_population, to_tidal, to_supercollider


def dummy_fitness(genome: Genome) -> float:
    """
    Dummy fitness function for testing.
    Returns a random fitness score.
    """
    import random
    return random.random()


def main():
    # Configuration
    population_size = 20
    num_generations = 10
    pattern_depth = 3
    synth_depth = 3
    
    print("=" * 60)
    print("Genetic Music Evolution - Basic Example")
    print("=" * 60)
    
    # Initialize population
    print(f"\nInitializing population of {population_size} individuals...")
    population = [
        Genome.random(pattern_depth=pattern_depth, synth_depth=synth_depth)
        for _ in range(population_size)
    ]
    
    # Show example genome
    print("\nExample genome:")
    print(f"  Pattern tree: {population[0].pattern_tree}")
    print(f"  Synth tree: {population[0].synth_tree}")
    
    # Show generated code
    print("\nGenerated Tidal code:")
    print(f"  {to_tidal(population[0].pattern_tree)}")
    
    print("\nGenerated SuperCollider code:")
    sc_code = to_supercollider(population[0].synth_tree, "example")
    print(f"  {sc_code[:200]}...")
    
    # Evolve
    print(f"\n{'=' * 60}")
    print("Starting evolution...")
    print(f"{'=' * 60}\n")
    
    evolved_population = evolve_population(
        population=population,
        fitness_fn=dummy_fitness,
        generations=num_generations,
        crossover_rate=0.8,
        mutation_rate=0.2,
        elite_size=2
    )
    
    # Show best individual
    best = max(evolved_population, key=lambda g: g.fitness)
    print(f"\n{'=' * 60}")
    print("Best individual:")
    print(f"  Fitness: {best.fitness:.4f}")
    print(f"  Pattern: {to_tidal(best.pattern_tree)}")
    print(f"  Synth depth: {best.synth_tree.depth()}")
    print(f"{'=' * 60}")
    
    print("\nEvolution complete!")


if __name__ == "__main__":
    main()

