# Genetic Co-Evolution of Music

A music generation system based on genetic programming that evolves both high-level musical structure (patterns, rhythm, arrangement) and low-level timbral design (synthesis, filters, envelopes, effects) using TidalCycles and SuperCollider.

## 🎯 Project Overview

This system co-evolves:
- **High-level structure**: Tidal-like pattern trees controlling rhythm, note order, repetition, and layering
- **Low-level timbre**: SuperDirt/SuperCollider synth trees defining synthesis, effects, envelopes, and parameters

The fitness function evaluates rendered sound using perceptual embeddings (CLAP, VGGish) or heuristics to guide evolution toward human-pleasant or dataset-similar audio.

## 🏗️ Architecture

```
Python GP Engine
   │
   ├── Pattern Tree ───────────▶ TidalCycles
   │   (rhythm, structure)      │
   │                            ├── interprets pattern
   │                            └── sends play events (OSC)
   │
   └── Synth Tree ─────────────▶ SuperDirt (SuperCollider)
       (timbre, effects)         │
                                 └── renders sound → WAV
                                         │
                                         ▼
                                   Fitness Evaluation
```

## 📁 Project Structure

```
genetic-coding/
├── src/genetic_music/      # Main source code
│   ├── genome.py           # Genome representation (PatternTree, SynthTree)
│   ├── codegen.py          # Code generation (Tree → Tidal/SC code)
│   ├── backend.py          # OSC communication with Tidal & SuperDirt
│   ├── fitness.py          # Audio-based fitness evaluation
│   ├── evolve.py           # Main evolutionary loop
│   └── utils.py            # Utility functions
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── data/                   # Data files
│   ├── audio/              # Audio samples
│   ├── reference/          # Reference datasets
│   └── outputs/            # Generated audio outputs
├── examples/               # Example usage scripts
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Setup

### Prerequisites

- Python 3.9+
- SuperCollider with SuperDirt
- TidalCycles (optional, for interactive testing)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd genetic-coding
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure SuperCollider:
   - Ensure SuperDirt is installed and running
   - Reserve orbit `/d8` for the GP system
   - Default port: 57120

## 🧬 Genome Structure

Each individual genome contains two symbolic trees:

```python
Genome(pattern_tree, synth_tree)
```

- **pattern_tree**: Built from Tidal combinators (fast, every, rev, stack, sound, etc.)
- **synth_tree**: Built from synthesis blocks (SinOsc, LPF, EnvGen, etc.)

### Example Pattern Tree
```
fast(2, every(3, rev, stack([sound("bd"), sound("sn cp")])))
```

### Example Synth Tree
```
LPF(Mix([SinOsc(440), Saw(330)]), 800)
```

## 🎛️ Communication

| Interface | Purpose | Port |
|-----------|---------|------|
| Python ↔ Tidal | Send pattern code | 6010 |
| Python ↔ SuperDirt | Load SynthDefs, control | 57120 |
| Tidal ↔ SuperDirt | Playback events | 57120 |

## 🎚️ Fast Iteration

To speed up evaluation:
- Accelerate playback (speed = 4 or higher)
- Record short clips (e.g., 2s)
- Optional: NRT rendering via `Score.recordNRT`

## 📊 Fitness Evaluation

Multiple fitness measures:
1. **Audio embedding similarity** (CLAP, VGGish) to reference dataset
2. **Perceptual heuristics** (spectral flatness, dynamic range, rhythmic energy)
3. **Human feedback** (interactive selection)
4. **Multi-objective**: Weighted combination of the above

## 🧪 Usage

```python
from genetic_music import Genome, evolve

# Initialize population
population = [Genome.random() for _ in range(50)]

# Run evolution
for generation in range(100):
    evolve(population, fitness_fn=audio_similarity)
```

## 🧪 Testing

The project includes comprehensive test suites for all components:

### Quick Start

```bash
# Run all tests
python tests/run_all_tests.py

# Run only unit tests (no external dependencies)
python tests/run_all_tests.py --unit

# Run integration tests (requires SuperCollider + SuperDirt)
python tests/run_all_tests.py --integration
```

### Individual Test Suites

```bash
# Unit tests (pytest)
pytest tests/test_genome.py -v
pytest tests/test_codegen.py -v

# Integration tests (manual)
python tests/test_supercollider.py  # Test SC server connectivity
python tests/test_superdirt.py      # Test SuperDirt audio playback
python tests/test_tidalcycles.py    # Test pattern generation
```

### Prerequisites for Integration Tests

1. **SuperCollider** must be running with **SuperDirt** started
2. See `scripts/setup_supercollider.md` for detailed setup instructions
3. Quick SuperDirt startup:
   ```supercollider
   (
   s.waitForBoot {
       ~dirt = SuperDirt(2, s);
       ~dirt.loadSoundFiles;
       ~dirt.start(57120, Array.fill(12, 0));
       "SuperDirt ready!".postln;
   };
   )
   ```

For detailed testing documentation, see `tests/README.md`.

### Smoke Test: Dual-Layer Communication

Run a minimal end-to-end check that sends a high-level Tidal pattern and then a low-level SuperCollider node:

```bash
source venv/bin/activate
python scripts/smoke_comm.py
```

It will:
- Generate a random pattern and synth
- Send the Tidal pattern to orbit `/d8`
- Spawn a `\default` synth node on scsynth briefly
- Apply a random mutation and repeat

### Dual-Layer Difference Test

Play the same pattern twice; the second pass adds a low-level overlay so it sounds different:

```bash
source venv/bin/activate
python scripts/test_dual_layer.py
```

### Shared High/Low Interface Test (Bus-Controlled)

Prereq: Load `scripts/sc/gpbus.scd` (your corrected version) in SuperCollider while SuperDirt is running.

Run:
```bash
source venv/bin/activate
python scripts/test_shared_interface.py
```
It plays one \gpbus note unmodified, then repeats while sweeping control buses (cutoff/res) from Python.

## 🔭 Future Enhancements

- [ ] Coevolution scheduler for high/low layer alternation
- [ ] Semantic mutation policies
- [ ] Hierarchical control mapping
- [ ] Parallel evaluation with multiple SuperDirt instances
- [ ] Interactive human-in-the-loop rating

## 📝 License

MIT

## 👥 Contributors

Federico Rubbi

