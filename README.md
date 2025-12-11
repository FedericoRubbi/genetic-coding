# Target-driven Genetic Programming of Music Patterns with TidalCycles

*Project for Bio-Inspired AI course, University of Trento* <br>
*Authors: Federico Rubbi, Jie Chen, Stefano Camposilvan, Valeria Miroslava Mayora Barcenas*

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Description

This project investigates how genetic programming can be used to automatically discover musical patterns in the live coding language TidalCycles such that their rendered audio approximates a given target recording. Rather than evolving music "in the abstract," we adopt a target-driven perspective: the goal is to search directly in the space of TidalCycles programs for patterns whose audio is as close as possible to a fixed example clip.

To make this feasible, we represent individuals as typed expression trees generated from a grammar that encodes a subset of the Tidal pattern language, ensuring that all genomes correspond to syntactically valid code. Each candidate pattern is rendered to audio via a TidalCycles/SuperDirt backend and evaluated with a composite fitness function that measures similarity to the target along multiple musical dimensions, including timbre, harmony, rhythm, dynamics, and tempo.

In summary, the project covers: (i) a grammar-based genome representation for genetic programming over TidalCycles patterns; (ii) a multi-feature audio similarity fitness tailored to this domain; and (iii) an empirical study of how these design choices influence the evolution of patterns toward a fixed audio target.

The full technical report is available in report/report.tex (LaTeX source).

## Features

- **Grammar-based Representation**: Ensures all evolved patterns are syntactically valid TidalCycles code through a context-free grammar with 239 production rules spanning 13 Lark modules.
- **Multi-Feature Fitness Evaluation**: Uses librosa for extracting MFCCs, chroma, onset strength, spectral features, RMS energy, and tempo estimates, aggregated into a scalar similarity score.
- **TidalCycles Integration**: Backend module handles OSC communication with TidalCycles and SuperDirt for pattern rendering and audio recording.
- **Musical Mutation Operators**: Suite of operators for structural changes (append, truncate, euclid), rhythmic transformations (speed, striate), layering (stack, overlay), and pitch/timbre modifications.
- **Configurable Evolution**: YAML-based configuration for population size, mutation rates, fitness weights, and Tidal settings.

## Installation

### Prerequisites
- Python 3.9 or higher
- TidalCycles installed and configured (https://tidalcycles.org/docs/)
- SuperDirt running (typically via SuperCollider) (https://supercollider.github.io/)
- Use `startup.scd` as SuperDirt starup file

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd genetic-coding
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure TidalCycles path in `config.yaml`:
   ```yaml
   tidal:
     boot_file_path: "/path/to/BootTidal.hs"
   ```

## Quick Start

### Basic Usage
```python
from genetic_music import Genome, to_tidal, Backend

# Create a random genome
g = Genome.random()

# Convert to Tidal code
tidal_code = to_tidal(g.pattern_tree)
print(tidal_code)

# Render audio (requires TidalCycles and SuperDirt running)
backend = Backend()
backend.play_tidal_code(tidal_code, duration=8.0)
backend.close()
```

### Running Evolution
```python
from genetic_music import evolve_population, load_audio, combined_fitness

# Load target audio
target_audio = load_audio("path/to/target.wav")

# Define fitness function
def fitness_fn(genome):
    audio = genome.render_audio()
    return combined_fitness(audio, target_audio)

# Evolve population
population = evolve_population(
    population_size=50,
    generations=100,
    fitness_fn=fitness_fn
)
```

See `examples/` for complete scripts.

## Project Architecture

The system is organized into focused subpackages under `src/genetic_music/`:

```
src/genetic_music/
├── grammar/          # Lark grammars for Tidal pattern types (13 modules, 239 rules)
├── tree/             # PatternTree and TreeNode classes
├── genome/           # Genome dataclass and population management
├── codegen/          # Tidal code generation from trees
├── backend/          # OSC communication with TidalCycles/SuperDirt
├── fitness_evaluation/ # Audio feature extraction and similarity
├── generator/        # Mutations, crossover, and evolution logic
│   └── mutations/    # Musical mutation operators
└── config.py         # Configuration management
```

### Data Flow
1. **Genome Generation**: Random pattern trees from grammar
2. **Code Generation**: Trees converted to TidalCycles strings
3. **Audio Rendering**: Code sent via OSC to TidalCycles/SuperDirt
4. **Fitness Evaluation**: Audio features compared to target
5. **Evolution**: Selection, crossover, mutation on population

See `docs/architecture.md` for detailed diagrams and component descriptions.

## Configuration

Settings are managed via `config.yaml` in the project root:

```yaml
# TidalCycles configuration
tidal:
  # Path to your BootTidal.hs file
  # You can use ~ for home directory, it will be expanded automatically
  boot_file_path: "~/.cabal/share/aarch64-osx-ghc-9.12.2-ea3d/tidal-1.10.1/BootTidal.hs"

# Backend configuration
backend:
  # GHCi command to use (default: "ghci")
  ghci_cmd: "ghci"
  
  # SuperDirt orbit for rendering
  orbit: 8
  
  # Dedicated Tidal stream number
  stream: 12

# Output paths
output:
  # Base directory for generated audio files
  audio_dir: "data/outputs"
  
  # Base directory for evolution results
  evolution_dir: "data/outputs/minimal_evolution"

```

Environment variables can override config values (e.g., `TIDAL_BOOT_FILE_PATH`).

## Examples

The `examples/` directory contains demonstration scripts:

- `minimal_evolution.py`: Basic evolution loop with audio rendering
- `minimal_evolution_save_wav.py`: Evolution with WAV file output
- `generation.py`: Pattern generation and mutation demos

Run examples after activating the virtual environment and ensuring TidalCycles is running.

## Dependencies

### Core Dependencies
- `numpy>=1.24.0`: Numerical computations
- `librosa>=0.10.0`: Audio feature extraction
- `python-osc>=1.8.0`: OSC communication
- `lark`: Grammar parsing
- `pyyaml>=6.0`: Configuration
- `tqdm>=4.65.0`: Progress bars

### Optional Dependencies
- `torch>=2.0.0`, `transformers>=4.30.0`: ML-based fitness (extras: ml)
- `matplotlib>=3.7.0`, `seaborn>=0.12.0`: Visualization (extras: viz)
- `pytest>=7.3.0`: Testing (extras: dev)

### External Requirements
- TidalCycles: Live coding environment
- SuperDirt: Audio synthesis engine
- SuperCollider: Audio server

Install optional dependencies: `pip install -e .[ml,viz,dev]`

## References

- Horner, A., & Goldberg, D. E. (1991). Genetic algorithms and computer-assisted music composition. In Proc. 4th Int. Conf. on Genetic Algorithms.
- McLean, A., & Wiggins, G. (2010). Tidal -- pattern language for the live coding of music. In Proc. 7th Sound and Music Computing Conf.
- McFee, B., et al. (2015). librosa: Audio and music signal analysis in python. In Proc. 14th Python in Science Conf.
- Full bibliography in `report/report.tex`

## Acknowledgments

- TidalCycles community for the live coding framework
- librosa developers for audio analysis tools
- Lark parser library for grammar support</content>
<filePath="README.md