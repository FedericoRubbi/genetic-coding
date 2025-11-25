"""Population evolution and selection logic."""

import random
from typing import List, Optional, Callable
from .genome import Genome


def evolve_population(
    population: List[Genome],
    fitness_func: Callable[[Genome], float],
    mutation_rate: float = 0.1,
    elitism: int = 1
) -> List[Genome]:
    """
    Evolve a population of genomes using mutation and selection.
    
    Args:
        population: List of genomes to evolve
        fitness_func: Function to evaluate genome fitness
        mutation_rate: Probability of mutation per genome
        elitism: Number of best individuals to preserve unchanged
    
    Returns:
        New population of evolved genomes
    """
    # Evaluate fitness for all genomes
    for genome in population:
        if genome.fitness == 0.0:  # Only evaluate if not already scored
            genome.fitness = fitness_func(genome)
    
    # Sort by fitness (descending)
    population.sort(key=lambda g: g.fitness, reverse=True)
    
    # Keep elite individuals
    new_population = population[:elitism]
    
    # Fill rest with mutations of better individuals
    while len(new_population) < len(population):
        # Select parent (bias towards fitter individuals)
        parent = population[int(random.random() ** 2 * len(population))]
        # Create mutated offspring
        offspring = parent.mutate(mutation_rate)

        if offspring.fitness == 0.0:
            offspring.fitness = fitness_func(offspring)
            
        new_population.append(offspring)
    
    return new_population