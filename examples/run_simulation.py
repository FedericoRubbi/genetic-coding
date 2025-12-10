"""Minimal example of pattern evolution with per-generation logging.

This script mirrors ``minimal_evolution_save_wav.py`` but focuses on running
an evolution over multiple generations and recording summary statistics
(min / max / mean fitness and best expression) for each generation using
``RunLogger``.

The resulting CSV and metadata JSON can be used later to create plots for
analysis or for inclusion in reports.
"""

from pathlib import Path

# --- Internal imports, updated for new package layout ---
from genetic_music.genome.genome import Genome
from genetic_music.genome.population import evolve_population
from genetic_music.generator import generate_expressions_mutational
from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.fitness_evaluation.fitness_evaluation import get_fitness
from genetic_music.run_logger import RunLogger


def main() -> None:
    # ---------------------------------------------------------------------
    # 1. Configuration
    # ---------------------------------------------------------------------
    pop_size = 32
    num_generations = 100
    mutation_rate = 1
    elitism = 2

    run_name = "run_simulation"

    # Where to store logs (CSV + metadata). ``RunLogger`` will create this.
    log_dir = Path("data/logs")

    print("Running minimal evolution with logging...")
    print(f"Population size: {pop_size}")
    print(f"Generations: {num_generations}")
    print(f"Mutation rate: {mutation_rate}")
    print(f"Elitism: {elitism}")
    print(f"Log directory: {log_dir.resolve()}")

    # ---------------------------------------------------------------------
    # 2. Initial population (PatternTree-based genomes)
    # ---------------------------------------------------------------------
    expressions = generate_expressions_mutational(pop_size)
    population = [Genome(pattern_tree=expression) for expression in expressions]

    # ---------------------------------------------------------------------
    # 3. Set up logger
    # ---------------------------------------------------------------------
    metadata = {
        "population_size": pop_size,
        "num_generations": num_generations,
        "mutation_rate": mutation_rate,
        "elitism": elitism,
        "fitness_func": "get_fitness",
        "note": "Example long-run evolution for plotting fitness over time.",
    }

    with RunLogger(run_name=run_name, output_dir=log_dir, metadata=metadata) as logger:
        # -----------------------------------------------------------------
        # 4. Evolution loop with per-generation logging
        # -----------------------------------------------------------------
        for gen in range(num_generations):
            population = evolve_population(
                population=population,
                fitness_func=get_fitness,
                mutation_rate=mutation_rate,
                elitism=elitism,
            )

            # Collect fitness scores and best individual.
            fitness_scores = [g.fitness for g in population]
            best = max(population, key=lambda g: g.fitness)
            best_expression = to_tidal(best.pattern_tree)

            logger.log_generation(
                generation=gen,
                fitness_scores=fitness_scores,
                best_expression=best_expression,
            )

            # Lightweight progress output.
            if gen % 10 == 0 or gen == num_generations - 1:
                print(
                    f"Generation {gen:4d} | "
                    f"best_fitness={best.fitness:.4f} | "
                    f"min={min(fitness_scores):.4f}, "
                    f"max={max(fitness_scores):.4f}, "
                    f"mean={sum(fitness_scores) / len(fitness_scores):.4f}"
                )

        print("\nEvolution completed.")
        print(f"CSV log written to: {logger.config.csv_path.resolve()}")
        print(f"Metadata written to: {logger.config.metadata_path.resolve()}")


if __name__ == "__main__":
    main()
