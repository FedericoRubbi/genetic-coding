# Genetic Evolution of Music

A system that evolves musical patterns using genetic programming and TidalCycles.

## Quick Start

### Prerequisites
- Python 3.9+
- TidalCycles
- SuperDirt

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd genetic-coding

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install in dev mode
pip install -e .
```

## Project Structure

```
genetic-coding/
├── src/genetic_music/     # Main source code
│   ├── genome.py         # Pattern tree representation
│   ├── codegen.py        # TidalCycles code generation
│   ├── backend.py        # OSC communication
│   ├── fitness.py        # Fitness evaluation
│   ├── evolve.py         # Evolutionary loop
│   └── utils.py         # Utilities
├── tests/               # Unit tests
├── examples/            # Example scripts
└── docs/               # Documentation
```

## Architecture

The system evolves pattern trees that represent TidalCycles code:

```python
# Example pattern tree
fast(2, every(3, rev, stack([sound("bd"), sound("sn cp")])))
```

Communication flow:
```
Python → TidalCycles (port 6010) → SuperDirt (port 57120) → Audio Output
```

## Usage

```python
from genetic_music import Genome, evolve_population

# Create initial population
population = [Genome.random() for _ in range(50)]

# Evolve
evolved = evolve_population(
    population,
    generations=100,
    fitness_fn=your_fitness_function
)
```

## Basic Example
```bash
python examples/basic_evolution.py
```

For more details, see the [architecture documentation](docs/architecture.md).
