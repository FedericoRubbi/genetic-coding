# Quick Start Guide

## Initial Setup

Your project structure is now ready! Here's what you need to do next:

### 1. Activate the Virtual Environment

```bash
cd /Users/federicorubbi/Documents/unitn/bio-inspired-artificial-intelligence/genetic-coding
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installing all dependencies (especially PyTorch and CLAP) may take a few minutes.

### 3. Install in Development Mode (Optional)

This allows you to import the package from anywhere:

```bash
pip install -e .
```

### 4. Verify Installation

Run the basic tests:

```bash
python tests/test_genome.py
python tests/test_codegen.py
```

You should see:
```
✓ Pattern tree created: ...
✓ Synth tree created: ...
✓ All tests passed!
```

### 5. Run the Basic Example

```bash
python examples/basic_evolution.py
```

This runs a simple evolution with a dummy fitness function (no SuperCollider required).

## Project Structure

```
genetic-coding/
├── src/genetic_music/      # Main source code
│   ├── genome.py           # Tree representation & genetic operators
│   ├── codegen.py          # Code generation (Tree → Tidal/SC)
│   ├── backend.py          # OSC communication
│   ├── fitness.py          # Fitness evaluation
│   ├── evolve.py           # Evolutionary loop
│   └── utils.py            # Utilities
├── tests/                  # Unit tests
├── examples/               # Example scripts
├── docs/                   # Documentation
├── data/                   # Data directories
├── scripts/                # Utility scripts
└── requirements.txt        # Dependencies
```

## Next Steps

### For Testing Without SuperCollider

You can run evolution with a dummy fitness function:

```bash
python examples/basic_evolution.py
```

This will evolve patterns and synths but won't actually render audio.

### For Full Setup With SuperCollider

1. **Install SuperCollider**: https://supercollider.github.io/
2. **Install SuperDirt**: See `scripts/setup_supercollider.md`
3. **Test OSC communication**: Try sending patterns from Python to SuperDirt
4. **Run full evolution**: Use real audio fitness evaluation

### To Start Development

1. Read `docs/getting_started.md` for detailed instructions
2. Review `docs/architecture.md` to understand the system
3. Modify `examples/config.yaml` for your experiments
4. Create your own evolution scripts

## Common Commands

```bash
# Activate environment
source venv/bin/activate

# Run tests
python -m pytest tests/

# Run example
python examples/basic_evolution.py

# Deactivate environment
deactivate
```

## Minimal Example

Here's a minimal working example (no SuperCollider needed):

```python
from genetic_music import Genome, evolve_population, to_tidal

# Create population
population = [Genome.random() for _ in range(10)]

# Dummy fitness
def fitness_fn(genome):
    # In real use, this would evaluate audio
    return len(to_tidal(genome.pattern_tree)) / 100

# Evolve
evolved = evolve_population(population, fitness_fn, generations=5)

# Print best
best = max(evolved, key=lambda g: g.fitness)
print(f"Best: {to_tidal(best.pattern_tree)}")
```

## Troubleshooting

### Virtual Environment Not Activated

If you see import errors, make sure you're in the virtual environment:

```bash
which python  # Should show: .../genetic-coding/venv/bin/python
```

If not:
```bash
source venv/bin/activate
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Want to Skip Heavy ML Dependencies?

Edit `requirements.txt` and comment out:
- torch
- transformers
- laion-clap

You can still use heuristic-based fitness without these.

## Ready to Go!

Your project is fully set up and ready for development. Start with:

```bash
source venv/bin/activate
python examples/basic_evolution.py
```

Then explore the documentation in `docs/` for more advanced usage.

Happy coding! 🎵🧬

