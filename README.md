# Genetic Evolution of Music

This project evolves musical patterns using genetic programming and TidalCycles.

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

## Project structure (refactored)

After refactoring the code was split into focused subpackages under `src/genetic_music/`.

```
src/genetic_music/
├── grammar/      # Function types, signatures and Tidal registry
├── tree/         # TreeNode and PatternTree generation
├── genome/       # Genome dataclass + population evolution
├── codegen/      # to_tidal() and code generation utilities
├── backend/      # Backend for Tidal/GHCi and SuperCollider OSC
└── __init__.py   # Top-level convenience exports

examples/
docs/
tests/
```

Notes:
- Legacy single-file modules that previously lived at the package root (e.g. `genome.py`, `codegen.py`, `backend.py`) have been split into the subpackages above.
- If you still have old imports targeting those top-level modules, update them to the new subpackage paths (examples below).

## Usage

Use the top-level convenience exports when possible (they re-export the most common symbols):

```python
from genetic_music import Genome, to_tidal, Backend, evolve_population

# Create a random genome
g = Genome.random()

# Convert to Tidal code
tidal_code = to_tidal(g.pattern_tree)

# Play/record (requires BootTidal.hs path and SuperDirt running)
backend = Backend(boot_tidal_path='/path/to/BootTidal.hs')
backend.play_tidal_code(tidal_code, duration=8.0)
backend.close()
```

Or import directly from subpackages:

```python
from genetic_music.tree.pattern_tree import PatternTree
from genetic_music.codegen.tidal_codegen import to_tidal
```

## Migration notes

- If you have existing code that does `from genetic_music import genome` or `from genetic_music import codegen`, update these to the new paths. Example mappings:
    - `genetic_music.genome` -> `genetic_music.genome.genome` (or `from genetic_music import Genome`)
    - `genetic_music.codegen` -> `genetic_music.codegen.tidal_codegen` (or `from genetic_music import to_tidal`)

- Recommended safe migration strategy:
    1. Create a backup folder for legacy files: `mkdir genetic_music_legacy` and move the old top-level modules there.
    2. Update import paths in your scripts to the new subpackage layout.
    3. Run the quick import test below to verify the package still imports correctly.

Quick import test (run in project root, after activating venv):

```bash
python -c "import genetic_music; print('OK', getattr(genetic_music, '__all__', None))"
```

## Examples

- See `examples/` for small scripts. The refactored `examples/minimal_evolution.py` demonstrates creating a population, converting patterns to Tidal, and using the `Backend` to play/record.

## More information

See `docs/architecture.md` for an extended architecture overview, data flow diagrams, and suggestions for extension.

If you'd like, I can:
- update example scripts to use the new imports,
- move legacy files into `genetic_music_legacy/`, or
- add a small smoke-test under `examples/` that verifies `to_tidal` on a random `PatternTree`.
