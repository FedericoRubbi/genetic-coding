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


### 4. Run the Basic Example

```bash
python examples/basic_evolution.py
```

This runs a simple evolution with a dummy fitness function.

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
