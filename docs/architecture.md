# Architecture Documentation

## Overview

The genetic music system consists of several interconnected components that work together to evolve musical patterns and synthesizer designs.

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
    │ - Recording     │
    │ - Playback      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │  External Systems               │
    │  - TidalCycles (port 6010)      │
    │  - SuperDirt (port 57120)       │
    │  - SuperCollider                │
    └─────────────────────────────────┘
```

## Data Flow

### 1. Initialization Phase

```
User → Evolution Config → Initialize Population
                          ├─ Random PatternTrees
                          └─ Random SynthTrees
```

### 2. Evaluation Phase

```
Genome → CodeGen → Executable Code
                   ├─ Tidal Pattern String

Executable Code → Backend → Play & Record
                            ├─ Send to TidalCycles
                            └─ Record Audio (WAV)

Audio File → Fitness Module → Fitness Score
             ├─ Load audio
             ├─ Extract features
             ├─ Compute embedding
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

## Module Responsibilities

### `genome.py`
- **Purpose**: Define genetic representation
- **Classes**: `TreeNode`, `PatternTree`, `Genome`
- **Key Methods**:
  - `random()`: Generate random trees
  - `mutate()`: Apply mutation operators
  - `crossover()`: Combine two genomes
  - Tree traversal and manipulation

### `codegen.py`
- **Purpose**: Translate symbolic trees to executable code
- **Functions**:
  - `to_tidal(tree)`: PatternTree → Tidal pattern string
- **Design**: Recursive tree traversal with code emission

### `backend.py`
- **Purpose**: Handle external system communication
- **Class**: `Backend`
- **Key Methods**:
  - `send_pattern()`: Send pattern to TidalCycles
  - `play_pattern()`: Orchestrate playback and recording
- **Communication**: OSC protocol via python-osc

### `fitness.py`
- **Purpose**: Evaluate audio quality
- **Functions**:
  - `compute_fitness()`: Main entry point
  - `heuristic_fitness()`: Rule-based evaluation
  - `embedding_similarity()`: ML-based similarity
  - `compute_spectral_features()`: Audio analysis
- **Methods**:
  - Heuristic (fast, no ML dependencies)
  - Embedding-based (CLAP, VGGish)
  - Combined (weighted mix)

### `evolve.py`
- **Purpose**: Orchestrate the evolutionary process
- **Functions**:
  - `evolve_population()`: Main evolution loop
  - `tournament_selection()`: Select parents
  - `roulette_selection()`: Fitness-proportionate selection
  - `crossover()`: Recombination operator
  - `mutate()`: Variation operator
- **Features**:
  - Elitism
  - Configurable operators
  - Progress tracking

## Communication Protocols

### OSC Message Format

#### To TidalCycles
```
Address: /d8
Arguments: [pattern_string]
Example: /d8 "fast 2 $ sound \"bd sn\""
```

### Audio Recording

```
SC → WAV file → Fitness evaluation
   │
   ├─ Sample rate: 44100 Hz
   ├─ Format: 16-bit PCM
   └─ Channels: Stereo (2)
```

## Configuration

### Evolution Parameters

```yaml
population_size: 50
num_generations: 100
crossover_rate: 0.8
mutation_rate: 0.1
elite_size: 2
selection_method: tournament  # or 'roulette'
```

### Tree Parameters

```yaml
pattern_depth: 4
generation_method: grow  # or 'full'
```

### Backend Parameters

```yaml
sc_host: 127.0.0.1
sc_port: 57120
tidal_host: 127.0.0.1
tidal_port: 6010
orbit: 8
recording_duration: 2.0
playback_speed: 4.0
```

### Fitness Parameters

```yaml
method: combined  # 'heuristic', 'embedding', or 'combined'
weights:
  heuristic: 0.6
  similarity: 0.4
```

## Extension Points

### Adding New Tidal Combinators

```python
# In genome.py
PatternTree.COMBINATORS.append('new_combinator')

# In codegen.py
def to_tidal(tree):
    # ...
    elif tree.op == 'new_combinator':
        # Generate code
        return f"new_combinator {args}"
```

### Adding Custom Fitness Functions

```python
# In fitness.py
def custom_fitness(audio: np.ndarray) -> float:
    # Your logic here
    return score

# In your evolution script
evolve_population(
    population,
    fitness_fn=lambda g: custom_fitness(play_and_record(g))
)
```

## Performance Considerations

### Fitness Evaluation Bottleneck
- **Issue**: Audio rendering is slow
- **Solutions**:
  - Accelerated playback (speed > 1)
  - Parallel evaluation (multiple SC instances)
  - Cached embeddings
  - NRT rendering

### Population Size vs. Quality
- Larger populations explore better but slower
- Recommended: 20-50 for interactive, 100-200 for batch

### Tree Depth
- Deeper trees = more complex music
- But: harder to train, slower to render
- Recommended: 3-5 levels

## Future Architecture Changes

### Planned Improvements
1. **Modular fitness pipeline**: Plug-and-play fitness components
2. **Distributed evaluation**: Remote workers for fitness
3. **Checkpointing**: Save/resume evolution
4. **Interactive GUI**: Real-time visualization and control
5. **Multi-objective optimization**: Pareto front exploration

