# Getting Started

This guide will help you get up and running with the genetic music evolution system.

## Prerequisites

- Python 3.9 or higher
- SuperCollider with SuperDirt installed
- (Optional) TidalCycles for interactive testing

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd genetic-coding
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Install in Development Mode (Optional)

```bash
pip install -e .
```

This allows you to import `genetic_music` from anywhere while developing.

## Quick Start

### Test the Installation

Run the basic tests:

```bash
python tests/test_genome.py
python tests/test_codegen.py
```

Expected output:
```
✓ Pattern tree created: ...
✓ Synth tree created: ...
✓ Genome created: ...
✓ All tests passed!
```

### Run the Basic Example

```bash
python examples/basic_evolution.py
```

This will:
1. Create a population of 20 random genomes
2. Evolve them for 10 generations using a dummy fitness function
3. Display the best individual

### Set Up SuperCollider

See `scripts/setup_supercollider.md` for detailed instructions.

Quick setup:

1. Open SuperCollider
2. Run this code:

```supercollider
(
s.options.numBuffers = 1024 * 256;
s.options.memSize = 8192 * 32;

s.waitForBoot {
    ~dirt = SuperDirt(2, s);
    ~dirt.loadSoundFiles;
    s.sync;
    ~dirt.start(57120, [0, 0, 0, 0, 0, 0, 0, 0, 8]);
    "SuperDirt ready for GP".postln;
};
)
```

## Your First Evolution

### 1. Create a Configuration File

Create `config.yaml`:

```yaml
evolution:
  population_size: 30
  num_generations: 20
  crossover_rate: 0.8
  mutation_rate: 0.15
  elite_size: 3

genome:
  pattern_depth: 3
  synth_depth: 3

backend:
  sc_host: "127.0.0.1"
  sc_port: 57120
  orbit: 8

fitness:
  method: "heuristic"  # Start simple
```

### 2. Write Your Evolution Script

Create `my_evolution.py`:

```python
from pathlib import Path
from genetic_music import (
    Genome, Backend, evolve_population,
    to_tidal, to_supercollider, compute_fitness
)

def main():
    # Initialize backend
    backend = Backend(orbit=8)
    
    # Create population
    population = [Genome.random() for _ in range(30)]
    
    # Define fitness function
    def fitness_fn(genome):
        # Generate code
        tidal_code = to_tidal(genome.pattern_tree)
        sc_code = to_supercollider(genome.synth_tree)
        
        # Send to SuperCollider/Tidal and record
        backend.send_synthdef(sc_code)
        audio_path = backend.play_pattern(
            tidal_code,
            duration=2.0,
            speed=4.0
        )
        
        # Compute fitness
        return compute_fitness(audio_path, method='heuristic')
    
    # Evolve
    final_population = evolve_population(
        population,
        fitness_fn=fitness_fn,
        generations=20
    )
    
    # Get best
    best = max(final_population, key=lambda g: g.fitness)
    print(f"\nBest fitness: {best.fitness:.4f}")
    print(f"Pattern: {to_tidal(best.pattern_tree)}")

if __name__ == "__main__":
    main()
```

### 3. Run It

```bash
python my_evolution.py
```

## Understanding the Output

### Console Output

```
Generation 1: Best=0.3421, Avg=0.1234
Generation 2: Best=0.4532, Avg=0.2341
...
Generation 20: Best=0.8765, Avg=0.6543

Best fitness: 0.8765
Pattern: fast 2 $ every 3 rev $ sound "bd sn cp"
```

### Generated Files

Audio files are saved in:
- `data/outputs/` - Final outputs
- `/tmp/genetic_music/` - Temporary files during evolution

## Next Steps

### Experiment with Different Fitness Functions

Try embedding-based fitness:

```python
# Requires torch and CLAP
def fitness_fn(genome):
    audio_path = backend.play_pattern(...)
    return compute_fitness(
        audio_path,
        reference_audio=reference,
        method='embedding'
    )
```

### Adjust Evolution Parameters

- Increase population size for better exploration
- Increase mutation rate for more variation
- Adjust tree depth for complexity

### Visualize Results

```python
import matplotlib.pyplot as plt

# Track fitness over generations
fitness_history = []

# ... in your evolution loop
fitness_history.append([ind.fitness for ind in population])

# Plot
plt.plot([max(gen) for gen in fitness_history])
plt.xlabel('Generation')
plt.ylabel('Best Fitness')
plt.show()
```

### Create a Reference Dataset

Collect audio samples you like and use them for similarity-based fitness:

```python
# Load reference audio
reference_audio = load_audio('data/reference/good_example.wav')

def fitness_fn(genome):
    audio_path = backend.play_pattern(...)
    generated_audio = load_audio(audio_path)
    return embedding_similarity(generated_audio, reference_audio)
```

## Troubleshooting

### "Connection refused" Error

SuperCollider might not be running or listening on the wrong port.

**Fix**: Ensure SuperCollider is running with SuperDirt on port 57120.

### No Audio Output

Check SuperCollider's audio setup:

```supercollider
ServerOptions.devices;  // List devices
s.options.device = "Your Device";
s.reboot;
```

### Import Errors

Make sure you're in the virtual environment:

```bash
which python  # Should show venv path
```

### Slow Evolution

Try these optimizations:
- Reduce `duration` in `play_pattern()`
- Increase `speed` multiplier
- Use `heuristic` fitness (faster than embeddings)
- Reduce population size for testing

## Resources

- [Architecture Documentation](architecture.md)
- [SuperCollider Setup](../scripts/setup_supercollider.md)
- [TidalCycles Documentation](https://tidalcycles.org/)
- [SuperCollider Documentation](https://doc.sccode.org/)

## Getting Help

If you encounter issues:
1. Check the error message carefully
2. Review the relevant documentation
3. Ensure all prerequisites are installed
4. Try the basic examples first
5. Check SuperCollider's console for errors

Happy evolving! 🎵🧬

