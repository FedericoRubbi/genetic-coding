"""Population evolution and selection logic."""

import random
import time
from typing import List, Optional, Callable
from .genome import Genome


def evolve_population(
    population: List[Genome],
    fitness_func: Callable[[Genome], float],
    mutation_rate: float = 0.1,
    elitism: int = 1,
    crossover_rate: float = 0.0,
) -> List[Genome]:
    """
    Evolve a population of genomes using mutation and selection.

    Args:
        population: List of genomes to evolve
        fitness_func: Function to evaluate genome fitness
        mutation_rate: Probability of mutation per genome
        elitism: Number of best individuals to preserve unchanged
        crossover_rate: Probability of generating offspring via crossover
            instead of single-parent mutation. If 0.0, evolution uses only
            mutation (current default behaviour).

    Returns:
        New population of evolved genomes
    """
    # Evaluate fitness for all genomes
    eval_start = time.time()
    initial_evals = 0
    for i, genome in enumerate(population):
        if genome.fitness == 0.0:  # Only evaluate if not already scored
            genome.fitness = fitness_func(genome)
            initial_evals += 1
    eval_time = time.time() - eval_start

    if initial_evals > 0:
        print(
            f"[Evolve] Evaluated {initial_evals}/{len(population)} initial genomes in {eval_time:.2f}s"
        )

    # Sort by fitness (descending)
    population.sort(key=lambda g: g.fitness, reverse=True)

    # Keep elite individuals
    new_population = population[:elitism]

    # Fill rest with mutations of better individuals
    offspring_needed = len(population) - elitism

    if offspring_needed > 0:
        print(f"[Evolve] Creating {offspring_needed} offspring (elitism={elitism})...")
        offspring_start = time.time()

        offspring_count = 0
        while len(new_population) < len(population):
            offspring_count += 1

            use_crossover = (
                crossover_rate > 0.0
                and len(population) >= 2
                and random.random() < crossover_rate
            )

            if use_crossover:
                # Select two parents (biased towards fitter individuals)
                parent_idx1 = int(random.random() ** 2 * len(population))
                parent_idx2 = int(random.random() ** 2 * len(population))
                parent1 = population[parent_idx1]
                parent2 = population[parent_idx2]

                child1, child2 = parent1.crossover(parent2)

                # Optionally mutate children as well, controlled by mutation_rate.
                child1 = child1.mutate(mutation_rate)
                child2 = child2.mutate(mutation_rate)

                if child1.fitness == 0.0:
                    child1.fitness = fitness_func(child1)
                new_population.append(child1)

                if len(new_population) < len(population):
                    if child2.fitness == 0.0:
                        child2.fitness = fitness_func(child2)
                    new_population.append(child2)

            else:
                # Select parent (bias towards fitter individuals)
                parent_idx = int(random.random() ** 2 * len(population))
                parent = population[parent_idx]

                # Create mutated offspring
                offspring = parent.mutate(mutation_rate)

                if offspring.fitness == 0.0:
                    offspring.fitness = fitness_func(offspring)

                new_population.append(offspring)

        offspring_time = time.time() - offspring_start
        print(
            f"[Evolve] Offspring complete in {offspring_time:.2f}s (avg {offspring_time/offspring_needed:.2f}s/individual)"
        )

    print(
        f"[Evolve] Best: {new_population[0].fitness:.4f}, Worst: {new_population[-1].fitness:.4f}"
    )

    return new_population
