# TidalCycles Grammar - Quick Reference

## Summary of Changes

### ✅ What Was Added

1. **Grammar System** (`genome.py`)
   - `FunctionType` enum - categorizes function signatures
   - `FunctionSignature` dataclass - defines function metadata
   - `TidalGrammar` class - central grammar definition

2. **Expanded Vocabulary**
   - **Functions**: 7 → 25 (+257% increase)
   - **Sound Samples**: 8 → 38 (+375% increase)

3. **Documentation**
   - `TIDAL_GRAMMAR.md` - Complete grammar documentation
   - `test_grammar.py` - Demonstration and testing script

### 🎵 New TidalCycles Functions

**Unary Transformers** (6 new):
- `palindrome`, `brak`, `degrade`, `shuffle`, `scramble`

**Time Manipulation** (5 new):
- `sparsity`, `hurry`, `ply`, `iter`, `chop`, `striate`

**Probabilistic** (2 new):
- `degradeBy`, `sometimesBy`

**Combinators** (4 new):
- `fastcat`, `slowcat`, `append`, `overlay`

**Conditional** (1 new):
- `whenmod`

### 🔊 New Sound Samples

**Drums**: 808bd, 808sd, 808hh, 808oh, 808cy, clap, click, cowbell, crash, cy, rim, tom

**Bass**: bass0-3, jungbass

**Synths**: superpiano, supersaw, supermandolin, supersquare

**Breaks**: breaks125, breaks152, breaks165, amencutup

**Other**: hand, tabla, industrial, insect, jazz

## Quick Usage

### Generate Random Patterns with New Grammar

```python
from genetic_music.genome import PatternTree, Genome

# Generate a pattern tree (uses grammar automatically)
pattern = PatternTree.random(max_depth=4, method='grow')

# Generate complete genome
genome = Genome.random(pattern_depth=4, synth_depth=4)
```

### Access Grammar Information

```python
from genetic_music.genome import TidalGrammar, FunctionType

# Get all functions
all_functions = TidalGrammar.get_all_functions()

# Get functions by type
unary_funcs = TidalGrammar.get_functions_by_type(FunctionType.UNARY)
numeric_funcs = TidalGrammar.get_functions_by_type(FunctionType.BINARY_NUMERIC)

# Get sound samples
sounds = TidalGrammar.SOUNDS
```

### Test the Grammar

```bash
# Run the test script
python examples/test_grammar.py
```

## How to Extend

### Adding a New Function

Edit `src/genetic_music/genome.py`:

```python
# Inside TidalGrammar.FUNCTIONS dictionary
'yourfunction': FunctionSignature(
    'yourfunction',
    FunctionType.UNARY,  # or BINARY_NUMERIC, etc.
    param_generator=lambda: random.uniform(0, 1),  # if needed
    min_children=1,
    max_children=1
),
```

### Adding New Sounds

Edit `src/genetic_music/genome.py`:

```python
# Inside TidalGrammar class
SOUNDS = [
    # ... existing sounds ...
    'newsound1', 'newsound2', 'newsound3',
]
```

## Architecture Benefits

### Before (Ad-hoc)
```python
# Hard-coded logic for each function
if op in ['fast', 'slow', 'density']:
    param = random.uniform(0.5, 4.0)
    child = cls.random(max_depth - 1, method)
    return cls(op, [child], param)
elif op == 'every':
    # Different logic
    ...
```

### After (Grammar-based)
```python
# Automatic handling based on signature
func_sig = random.choice(TidalGrammar.get_all_functions())
param = func_sig.generate_param()  # Automatic
children = [cls.random(...) for _ in range(func_sig.get_num_children())]
return cls(func_sig.name, children, param)
```

## Key Files

- `src/genetic_music/genome.py` - Grammar implementation
- `docs/TIDAL_GRAMMAR.md` - Detailed documentation
- `examples/test_grammar.py` - Test and demonstration
- `docs/QUICK_REFERENCE_GRAMMAR.md` - This file

## Next Steps

1. **Test code generation**: Ensure `codegen.py` can handle new functions
2. **Add more functions**: See TidalCycles documentation for ideas
3. **Add effect parameters**: Extend grammar for `# delay`, `# gain`, etc.
4. **Implement mini-notation**: Add support for pattern strings

## Resources

- [TidalCycles Docs](https://tidalcycles.org/docs/)
- [Control Functions](https://userbase.tidalcycles.org/Control_Functions.html)
- [All Effects](https://userbase.tidalcycles.org/All_effects_and_synths.html)
- [Community Forum](https://club.tidalcycles.org/)

