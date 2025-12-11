"""Population evolution and selection logic."""

import random
import time
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
    eval_start = time.time()
    initial_evals = 0
    for i, genome in enumerate(population):
        if genome.fitness == 0.0:  # Only evaluate if not already scored
            genome.fitness = fitness_func(genome)
            initial_evals += 1
    eval_time = time.time() - eval_start
    
    if initial_evals > 0:
        print(f"[Evolve] Evaluated {initial_evals}/{len(population)} initial genomes in {eval_time:.2f}s")
    
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
            
            # Select parent (bias towards fitter individuals)
            parent_idx = int(random.random() ** 2 * len(population))
            parent = population[parent_idx]
            
            # Create mutated offspring
            offspring = parent.mutate(mutation_rate)

            if offspring.fitness == 0.0:
                offspring.fitness = fitness_func(offspring)
                
            new_population.append(offspring)
        
        offspring_time = time.time() - offspring_start
        print(f"[Evolve] Offspring complete in {offspring_time:.2f}s (avg {offspring_time/offspring_needed:.2f}s/individual)")
    
    print(f"[Evolve] Best: {new_population[0].fitness:.4f}, Worst: {new_population[-1].fitness:.4f}")
    
    return new_population