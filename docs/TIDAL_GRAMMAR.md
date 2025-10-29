# TidalCycles Grammar System

This document explains the grammar-based system for TidalCycles pattern generation in the genetic music system.

## Overview

The `TidalGrammar` class defines a formal grammar for TidalCycles functions, specifying:
- Available functions and their names
- Function signature types (how many arguments, what types)
- Parameter generation rules (numeric ranges, distributions)
- Child pattern requirements

This allows the genetic algorithm to generate syntactically correct TidalCycles patterns.

## Architecture

### Function Types

The system categorizes TidalCycles functions into six signature types:

```python
class FunctionType(Enum):
    UNARY = "unary"                    # (pattern) -> pattern
    BINARY_NUMERIC = "binary_numeric"  # (number, pattern) -> pattern
    BINARY_INT = "binary_int"          # (int, pattern) -> pattern
    N_ARY = "n_ary"                    # (pattern, ...) -> pattern
    CONDITIONAL = "conditional"        # (int, pattern, pattern) -> pattern
    PROBABILISTIC = "probabilistic"    # (float[0-1], pattern) -> pattern
```

### Function Signature

Each function is defined by a `FunctionSignature` object:

```python
@dataclass
class FunctionSignature:
    name: str                           # Function name (e.g., "fast", "rev")
    func_type: FunctionType             # Signature type
    param_generator: Callable           # Generates numeric/int parameters
    min_children: int = 1               # Minimum pattern children
    max_children: int = 1               # Maximum pattern children
```

## Current Grammar

### Unary Transformers
Functions that transform a single pattern: `(pattern) -> pattern`

- `rev` - Reverse pattern
- `palindrome` - Pattern forwards then backwards
- `brak` - Breakbeat transformation
- `degrade` - Randomly remove events
- `shuffle` - Shuffle pattern events
- `scramble` - Scramble pattern structure

### Binary Numeric
Functions with a numeric parameter: `(number, pattern) -> pattern`

- `fast(n)` - Speed up by factor n (0.5-4.0)
- `slow(n)` - Slow down by factor n (0.5-4.0)
- `density(n)` - Change event density (0.5-4.0)
- `sparsity(n)` - Reduce event density (0.5-4.0)
- `hurry(n)` - Speed up and pitch up (0.5-2.0)

### Binary Integer
Functions with an integer parameter: `(int, pattern) -> pattern`

- `ply(n)` - Repeat each event n times (2-4)
- `iter(n)` - Rotate pattern n times (2-8)
- `chop(n)` - Chop into n pieces (2-16)
- `striate(n)` - Striate into n parts (2-16)

### Probabilistic
Functions with probability parameter: `(float, pattern) -> pattern`

- `degradeBy(p)` - Remove events with probability p (0.1-0.7)
- `sometimesBy(p)` - Apply transformation with probability p (0.2-0.8)

### N-ary Combinators
Functions combining multiple patterns: `(pattern, pattern, ...) -> pattern`

- `stack` - Layer patterns (2-4 patterns)
- `cat` - Concatenate patterns sequentially (2-4 patterns)
- `fastcat` - Fast concatenate (2-4 patterns)
- `slowcat` - Slow concatenate (2-4 patterns)
- `append` - Append two patterns (exactly 2 patterns)
- `overlay` - Overlay patterns (2-3 patterns)

### Conditional
Functions with conditional logic: `(int, pattern, pattern) -> pattern`

- `every(n, transform, pattern)` - Apply transform every n cycles (n: 2-8)
- `whenmod(n, transform, pattern)` - Apply when cycle mod n (n: 3-8)

## How to Add New Functions

### Step 1: Identify the Function Type

Determine which `FunctionType` matches your function's signature:

**Example**: Adding `jux` (applies transformation to right channel only)
- Signature: `jux(transform, pattern) -> pattern`
- Type: Similar to UNARY but with transformation parameter
- We can use BINARY_PATTERN or add a new type

### Step 2: Define the Function Signature

Add to `TidalGrammar.FUNCTIONS`:

```python
'jux': FunctionSignature(
    'jux',
    FunctionType.UNARY,  # Takes one pattern, applies transformation
    min_children=1,
    max_children=1
),
```

### Step 3: Add Parameter Generator (if needed)

For functions with numeric/int parameters:

```python
'gap': FunctionSignature(
    'gap',
    FunctionType.BINARY_INT,
    param_generator=lambda: random.randint(2, 8),  # Gap size
    min_children=1,
    max_children=1
),
```

### Step 4: Update Code Generation

Ensure `codegen.py` can handle your new function when generating TidalCycles code.

## Adding New Sound Samples

Simply add to `TidalGrammar.SOUNDS`:

```python
SOUNDS = [
    # Drums
    'bd', 'sn', 'cp', 'hh', 'oh', 'ch', 'cy', 'rim', 'tom',
    # Add your new sounds here
    'mynewsample', 'anothersound',
    ...
]
```

## Complex Example: Adding `stut` (Stutter/Echo)

`stut` has signature: `stut(repeats, decay, delay, pattern)`
- `repeats`: int (number of echoes)
- `decay`: float (volume decay)
- `delay`: float (time between echoes)
- `pattern`: pattern to stutter

This requires multiple parameters. Options:

### Option 1: Create a new function type

```python
class FunctionType(Enum):
    ...
    STUTTER = "stutter"  # (int, float, float, pattern) -> pattern
```

### Option 2: Encode parameters in value

```python
'stut': FunctionSignature(
    'stut',
    FunctionType.BINARY_NUMERIC,
    param_generator=lambda: {
        'repeats': random.randint(2, 8),
        'decay': random.uniform(0.5, 0.9),
        'delay': random.uniform(0.0625, 0.25)
    },
    min_children=1,
    max_children=1
),
```

Then update `codegen.py` to unpack the dictionary.

## Reference: TidalCycles Documentation

- Official Docs: https://tidalcycles.org/docs/
- Control Functions: https://userbase.tidalcycles.org/Control_Functions.html
- Mini Notation: https://userbase.tidalcycles.org/Mini_notation_syntax.html
- Effects & Synths: https://userbase.tidalcycles.org/All_effects_and_synths.html

## Tips for Extension

1. **Start Simple**: Add functions with existing types first
2. **Test Generation**: Create test genomes and verify syntax
3. **Consider Musically**: Not all TidalCycles functions are useful for evolution
4. **Balance Complexity**: Too many functions may dilute the search space
5. **Group by Purpose**: Time transforms, structure changes, effects, etc.

## Current Limitations

1. **Effect Parameters**: Functions like `# delay 0.5` are not yet represented
2. **Mini-notation**: String patterns like `"bd*4 sn"` not yet supported
3. **Arithmetic Patterns**: `"<1 2 3>"` style sequences not yet included
4. **Continuous Parameters**: Most parameters are fixed at generation time

These could be future extensions to the grammar system.

