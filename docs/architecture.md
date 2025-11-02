# Architecture Documentation

## Overview

The genetic music system evolves TidalCycles patterns through genetic programming.

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Evolutionary Loop                     │
│                     (evolve.py)                         │
└─────────────┬───────────────────────────┬───────────────┘
              │                           │
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │  Genome Module  │         │ Fitness Module  │
    │  (genome.py)    │         │  (fitness.py)   │
    │                 │         │                 │
    │ - PatternTree   │         │ - Audio loading │
    │ - Mutation      │         │ - Feature extr. │
    │ - Crossover     │         │ - Embedding sim.│
    └────────┬────────┘         │ - Heuristics    │
             │                  └───────┬─────────┘
             │                          │
             ▼                          │
    ┌─────────────────┐                 │
    │  CodeGen Module │                 │
    │  (codegen.py)   │                 │
    │                 │                 │
    │ - to_tidal()    │                 │
    └────────┬────────┘                 │
             │                          │
             ▼                          │
    ┌─────────────────┐                 │
    │ Backend Module  │◄────────────────┘
    │  (backend.py)   │
    │                 │
    │ - OSC comms     │
    │ - Audio         │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │  External Systems               │
    │  - TidalCycles (port 6010)      │
    │  - SuperDirt (port 57120)       │
    └─────────────────────────────────┘
```

## Data Flow

### 1. Initialization Phase

```
User → Evolution Config → Initialize Population
                          └─ Random PatternTrees
```

### 2. Evaluation Phase

```
PatternTree → CodeGen → Tidal Pattern String → Backend → Play & Record
                                                        └─ TidalCycles

Audio File → Fitness Module → Fitness Score
             ├─ Load audio
             ├─ Extract features
             └─ Calculate fitness
```

### 3. Evolution Phase

```
Population + Fitness Scores → Selection
                              ├─ Tournament
                              └─ Roulette

Selected Parents → Genetic Operators
                   ├─ Crossover
                   └─ Mutation

New Offspring → New Population
```

## Core Modules

### `genome.py`
- Pattern tree representation and operations
- `PatternTree`: TidalCycles pattern structure
- `TreeNode`: Base tree functionality
- `Genome`: Wrapper for evolution

### `codegen.py`
- Converts trees to TidalCycles code
- `to_tidal()`: Tree → pattern string
- Recursive code generation

### `backend.py`
- OSC communication with TidalCycles
- Pattern sending & playback
- Audio recording

### `fitness.py`
- Audio quality evaluation
- Feature extraction
- ML-based similarity
- Heuristic measures

### `evolve.py`
- Evolution orchestration
- Selection & variation
- Population management
- Progress tracking

## Communication

### OSC Protocol
```
To TidalCycles: 
  Address: /d8
  Args: [pattern_string]
  Example: /d8 "fast 2 $ sound \"bd sn\""
```

## Configuration

```yaml
# Evolution
population_size: 50
generations: 100
crossover_rate: 0.8
mutation_rate: 0.1
elite_size: 2

# Pattern Generation
pattern_depth: 4
method: grow  # or 'full'

# Communication
tidal_port: 6010
orbit: 8

# Fitness
method: combined
weights:
  heuristic: 0.6
  similarity: 0.4
```

## Extensions

### New Pattern Functions
```python
# In genome.py
TidalGrammar.FUNCTIONS['new_fn'] = FunctionSignature(...)

# In codegen.py
def to_tidal(tree):
    if tree.op == 'new_fn':
        return f"new_fn {args}"
```

### Custom Fitness
```python
def my_fitness(audio: np.ndarray) -> float:
    return compute_features(audio)

evolve_population(population, fitness_fn=my_fitness)
```

## Optimization Tips

- Use faster playback (speed > 1)
- Keep patterns simple (3-5 levels)
- Start with small populations (20-50)
- Cache fitness evaluations

