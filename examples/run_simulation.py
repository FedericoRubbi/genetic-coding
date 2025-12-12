"""Minimal example of pattern evolution with per-generation logging.

This script mirrors ``minimal_evolution_save_wav.py`` but focuses on running
an evolution over multiple generations and recording summary statistics
(min / max / mean fitness and best expression) for each generation using
``RunLogger``.

The resulting CSV and metadata JSON can be used later to create plots for
analysis or for inclusion in reports.
"""

import sys
from pathlib import Path
import time

# --- Internal imports, updated for new package layout ---
from genetic_music.genome.genome import Genome
from genetic_music.genome.population import evolve_population
from genetic_music.generator import generate_expressions_mutational
from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.fitness_evaluation.fitness_evaluation import get_fitness
from genetic_music.run_logger import RunLogger
from genetic_music.checkpoint import save_checkpoint, load_checkpoint


def main() -> None:
    # Ensure stdout is flushed immediately so supervisor sees progress
    sys.stdout.reconfigure(line_buffering=True)

    # ---------------------------------------------------------------------
    # 1. Configuration
    # ---------------------------------------------------------------------
    # For testing: small pop, few generations
    pop_size = 32  # Small population for testing
    num_generations = 200  # Few generations for quick testing
    mutation_rate = 0.95
    crossover_rate = 0.5  # Probability of using crossover for offspring
    elitism = 2  # Keep 2 best, create 6 new offspring per generation

    run_name = "run_simulation"

    # Where to store logs (CSV + metadata). ``RunLogger`` will create this.
    log_dir = Path("data/logs")
    checkpoint_path = Path("data/checkpoints/latest.pkl")

    print("Running minimal evolution with logging...")
    print(f"Population size: {pop_size}")
    print(f"Generations: {num_generations}")
    print(f"Mutation rate: {mutation_rate}")
    print(f"Crossover rate: {crossover_rate}")
    print(f"Elitism: {elitism}")
    print(f"Log directory: {log_dir.resolve()}")
    print(f"Checkpoint path: {checkpoint_path.resolve()}")

    # ---------------------------------------------------------------------
    # 2. Initial population (Load from Checkpoint if available)
    # ---------------------------------------------------------------------
    start_gen = 0
    population = None

    if checkpoint_path.exists():
        try:
            print(f"[Resume] Found checkpoint at {checkpoint_path}")
            loaded_gen, loaded_pop, _ = load_checkpoint(checkpoint_path)
            start_gen = loaded_gen + 1
            population = loaded_pop
            print(f"[Resume] Loaded population size: {len(population)}")
            print(
                f"[Resume] Resuming from generation {start_gen + 1}/{num_generations}"
            )
        except Exception as e:
            print(f"[Resume] ERROR loading checkpoint: {e}")
            print("[Resume] Starting fresh...")
            population = None

    if population is None:
        print("[Init] Generating fresh population...")
        expressions = generate_expressions_mutational(pop_size)
        population = [Genome(pattern_tree=expression) for expression in expressions]

    if start_gen >= num_generations:
        print(
            f"[Run] Simulation already completed (last gen {start_gen} >= {num_generations})."
        )
        return

    # ---------------------------------------------------------------------
    # 3. Set up logger
    # ---------------------------------------------------------------------
    metadata = {
        "population_size": pop_size,
        "num_generations": num_generations,
        "mutation_rate": mutation_rate,
        "crossover_rate": crossover_rate,
        "elitism": elitism,
        "fitness_func": "get_fitness",
        "note": "Example long-run evolution for plotting fitness over time.",
        "resumed_from_gen": start_gen,
    }

    # RunLogger creates a new file with timestamp.
    # If resuming, this will be a new "segment" of the log.
    with RunLogger(run_name=run_name, output_dir=log_dir, metadata=metadata) as logger:
        # -----------------------------------------------------------------
        # 4. Evolution loop with per-generation logging
        # -----------------------------------------------------------------
        for gen in range(start_gen, num_generations):
            gen_start = time.time()
            print(f"\n[Run] Starting generation {gen + 1}/{num_generations}")

            population = evolve_population(
                population=population,
                fitness_func=get_fitness,
                mutation_rate=mutation_rate,
                elitism=elitism,
                crossover_rate=crossover_rate,
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

            # Save Checkpoint
            save_checkpoint(
                filepath=checkpoint_path, generation=gen, population=population
            )

            gen_time = time.time() - gen_start
            print(
                f"[Run] Finished generation {gen + 1}/{num_generations} "
                f"in {gen_time:.2f}s "
                f"(best_fitness={best.fitness:.4f})"
            )

        print("\nEvolution completed.")
        print(f"CSV log written to: {logger.config.csv_path.resolve()}")
        print(f"Metadata written to: {logger.config.metadata_path.resolve()}")


if __name__ == "__main__":
    main()
