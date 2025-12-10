# Target-driven Genetic Programming of Music Patterns with TidalCycles

*A Bio-Inspired AI Project for Automatic Music Generation*

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Description

This project investigates how genetic programming can be used to automatically discover musical patterns in the live coding language TidalCycles such that their rendered audio approximates a given target recording. Rather than evolving music "in the abstract," we adopt a target-driven perspective: the goal is to search directly in the space of TidalCycles programs for patterns whose audio is as close as possible to a fixed example clip.

To make this feasible, we represent individuals as typed expression trees generated from a grammar that encodes a subset of the Tidal pattern language, ensuring that all genomes correspond to syntactically valid code. Each candidate pattern is rendered to audio via a TidalCycles/SuperDirt backend and evaluated with a composite fitness function that measures similarity to the target along multiple musical dimensions, including timbre, harmony, rhythm, dynamics, and tempo.

In summary, the project covers: (i) a grammar-based genome representation for genetic programming over TidalCycles patterns; (ii) a multi-feature audio similarity fitness tailored to this domain; and (iii) an empirical study of how these design choices influence the evolution of patterns toward a fixed audio target.

This is a university project for the BIO-INSPIRED AI course.

## Features

- **Grammar-based Representation**: Ensures all evolved patterns are syntactically valid TidalCycles code through a context-free grammar with 239 production rules spanning 13 Lark modules.
- **Multi-Feature Fitness Evaluation**: Uses librosa for extracting MFCCs, chroma, onset strength, spectral features, RMS energy, and tempo estimates, aggregated into a scalar similarity score.
- **TidalCycles Integration**: Backend module handles OSC communication with TidalCycles and SuperDirt for pattern rendering and audio recording.
- **Musical Mutation Operators**: Suite of operators for structural changes (append, truncate, euclid), rhythmic transformations (speed, striate), layering (stack, overlay), and pitch/timbre modifications.
- **Configurable Evolution**: YAML-based configuration for population size, mutation rates, fitness weights, and Tidal settings.

## Installation

### Prerequisites
- Python 3.9 or higher
- TidalCycles installed and configured
- SuperDirt running (typically via SuperCollider)
- Optional: Machine learning dependencies for advanced fitness evaluation

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
evolution:
  population_size: 50
  generations: 100
  crossover_rate: 0.8
  mutation_rate: 0.1
  elite_size: 2

tidal:
  boot_file_path: "~/path/to/BootTidal.hs"
  port: 6010
  orbit: 8

fitness:
  method: combined
  weights:
    timbre: 0.4
    harmony: 0.3
    rhythm: 0.2
    dynamics: 0.1
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

## Development

### Testing
```bash
pytest
```

### Code Quality
```bash
black src/ examples/
flake8 src/ examples/
```

### Grammar Visualization
Explore the Tidal grammars visually:
```bash
python -m utils.grammar_viz --root src/genetic_music/grammar --out grammar_graph.html
```

## Academic Context

This project was developed as part of the BIO-INSPIRED AI course at [University Name]. The full technical report is available in `report/report.tex` (LaTeX source).

The approach builds on evolutionary music systems (e.g., Horner 1991, Papadopoulos 1999) and live coding integration (e.g., Hickinbotham 2016), extending them with target-driven audio similarity objectives.

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure compatibility with Python 3.9+

## License

MIT License - see LICENSE file for details.

## Authors

- [Your Name] - Project Developer
- Course: BIO-INSPIRED AI
- Supervisor: [Supervisor Name, if applicable]

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