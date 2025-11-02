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
   └── Pattern Tree ───────────▶ TidalCycles
       (rhythm, structure)      │
                                ├── interprets pattern
                                ├── sends play events (OSC)
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
- TidalCycles

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
   - Default port: 57120

## 🧬 Genome Structure

Each individual genome contains a symbolic tree:

```python
Genome(pattern_tree)
```

- **pattern_tree**: Built from Tidal combinators (fast, every, rev, stack, sound, etc.)

### Example Pattern Tree
```
fast(2, every(3, rev, stack([sound("bd"), sound("sn cp")])))
```

## 🎛️ Communication

| Interface | Purpose | Port |
|-----------|---------|------|
| Python ↔ Tidal | Send pattern code | 6010 |
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
