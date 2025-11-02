"""
Main evolutionary loop and genetic operators.

Implements selection, crossover, mutation, and population management.
"""

import random
from typing import List, Callable, Tuple
from .genome import Genome


def tournament_selection(
    population: List[Genome],
    tournament_size: int = 3
) -> Genome:
    """
    Select an individual using tournament selection.
    
    Args:
        population: Population to select from
        tournament_size: Number of individuals in tournament
    
    Returns:
        Selected genome
    """
    tournament = random.sample(population, tournament_size)
    return max(tournament, key=lambda g: g.fitness)


def roulette_selection(population: List[Genome]) -> Genome:
    """
    Select an individual using fitness-proportionate selection.
    
    Args:
        population: Population to select from
    
    Returns:
        Selected genome
    """
    total_fitness = sum(ind.fitness for ind in population)
    if total_fitness == 0:
        return random.choice(population)
    
    pick = random.uniform(0, total_fitness)
    current = 0
    for ind in population:
        current += ind.fitness
        if current >= pick:
            return ind
    
    return population[-1]


def crossover(parent1: Genome, parent2: Genome) -> Tuple[Genome, Genome]:
    """
    Perform crossover between two pattern trees.
    
    Args:
        parent1: First parent
        parent2: Second parent
    
    Returns:
        Two offspring genomes
    """
    # TODO: Implement pattern tree crossover
    # For now, return clones
    offspring1 = Genome(
        pattern_tree=parent1.pattern_tree
    )
    offspring2 = Genome(
        pattern_tree=parent2.pattern_tree
    )
    return offspring1, offspring2


def mutate(genome: Genome, mutation_rate: float = 0.1) -> Genome:
    """
    Mutate a genome.
    
    Args:
        genome: Genome to mutate
        mutation_rate: Probability of mutation
    
    Returns:
        Mutated genome (new instance)
    """
    # TODO: Implement tree mutation
    # Options:
    # - Point mutation (change node value)
    # - Subtree mutation (replace subtree with random tree)
    # - Node mutation (change operation)
    
    return genome


def evolve_population(
    population: List[Genome],
    fitness_fn: Callable[[Genome], float],
    generations: int = 1,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    elite_size: int = 2,
    selection_method: str = 'tournament'
) -> List[Genome]:
    """
    Evolve a population for one or more generations.
    
    Args:
        population: Initial population
        fitness_fn: Fitness evaluation function
        generations: Number of generations to evolve
        crossover_rate: Probability of crossover
        mutation_rate: Probability of mutation
        elite_size: Number of elite individuals to preserve
        selection_method: 'tournament' or 'roulette'
    
    Returns:
        Evolved population
    """
    pop_size = len(population)
    
    for gen in range(generations):
        # Evaluate fitness
        for ind in population:
            if ind.fitness == 0:  # Only evaluate if not already evaluated
                ind.fitness = fitness_fn(ind)
        
        # Sort by fitness
        population.sort(key=lambda g: g.fitness, reverse=True)
        
        # Statistics
        best_fitness = population[0].fitness
        avg_fitness = sum(g.fitness for g in population) / len(population)
        print(f"Generation {gen + 1}: Best={best_fitness:.4f}, Avg={avg_fitness:.4f}")
        
        # Elitism: preserve best individuals
        new_population = population[:elite_size]
        
        # Selection function
        if selection_method == 'tournament':
            select_fn = lambda: tournament_selection(population)
        else:
            select_fn = lambda: roulette_selection(population)
        
        # Generate offspring
        while len(new_population) < pop_size:
            parent1 = select_fn()
            parent2 = select_fn()
            
            if random.random() < crossover_rate:
                offspring1, offspring2 = crossover(parent1, parent2)
            else:
                offspring1, offspring2 = parent1, parent2
            
            if random.random() < mutation_rate:
                offspring1 = mutate(offspring1, mutation_rate)
            if random.random() < mutation_rate:
                offspring2 = mutate(offspring2, mutation_rate)
            
            new_population.extend([offspring1, offspring2])
        
        # Trim to population size
        population = new_population[:pop_size]
    
    return population

