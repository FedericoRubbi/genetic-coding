# TidalCycles Grammar - Visual Reference

## 🗺️ Quick Navigation

```
GRAMMAR SYSTEM
│
├── 📖 Documentation
│   ├── TIDAL_GRAMMAR.md ..................... Complete guide
│   ├── QUICK_REFERENCE_GRAMMAR.md ........... Quick reference
│   ├── GRAMMAR_IMPLEMENTATION_SUMMARY.md .... Implementation details
│   └── GRAMMAR_VISUAL_REFERENCE.md .......... This file
│
├── 🧬 Code
│   ├── src/genetic_music/genome.py .......... Grammar implementation
│   └── src/genetic_music/codegen.py ......... Code generation
│
└── 🧪 Examples & Tests
    ├── examples/test_grammar.py ............. Grammar demonstration
    └── examples/test_codegen_grammar.py ..... Code generation test
```

## 🎵 Function Type Hierarchy

```
TidalCycles Functions (25 total)
│
├── UNARY (6 functions)
│   │   Signature: (pattern) -> pattern
│   │   Syntax: op (pattern)
│   │
│   ├── rev ........................ Reverse pattern
│   ├── palindrome ................. Forward then backward
│   ├── brak ....................... Breakbeat transform
│   ├── degrade .................... Random event removal
│   ├── shuffle .................... Shuffle events
│   └── scramble ................... Scramble structure
│
├── BINARY_NUMERIC (5 functions)
│   │   Signature: (number, pattern) -> pattern
│   │   Syntax: op value $ pattern
│   │
│   ├── fast (0.5-4.0) ............. Speed up
│   ├── slow (0.5-4.0) ............. Slow down
│   ├── density (0.5-4.0) .......... Change density
│   ├── sparsity (0.5-4.0) ......... Reduce density
│   └── hurry (0.5-2.0) ............ Speed + pitch
│
├── BINARY_INT (4 functions)
│   │   Signature: (int, pattern) -> pattern
│   │   Syntax: op value $ pattern
│   │
│   ├── ply (2-4) .................. Repeat events
│   ├── iter (2-8) ................. Rotate pattern
│   ├── chop (2-16) ................ Chop sample
│   └── striate (2-16) ............. Striate sample
│
├── PROBABILISTIC (2 functions)
│   │   Signature: (float[0-1], pattern) -> pattern
│   │   Syntax: op probability $ pattern
│   │
│   ├── degradeBy (0.1-0.7) ........ Remove with probability
│   └── sometimesBy (0.2-0.8) ...... Apply with probability
│
├── N_ARY (6 functions)
│   │   Signature: (pattern, ...) -> pattern
│   │   Syntax: op [pattern1, pattern2, ...]
│   │
│   ├── stack (2-4 children) ....... Layer patterns
│   ├── cat (2-4 children) ......... Concatenate sequential
│   ├── fastcat (2-4 children) ..... Fast concatenate
│   ├── slowcat (2-4 children) ..... Slow concatenate
│   ├── append (2 children) ........ Append two patterns
│   └── overlay (2-3 children) ..... Overlay patterns
│
└── CONDITIONAL (2 functions)
    │   Signature: (int, pattern, pattern) -> pattern
    │   Syntax: op n (transform) $ pattern
    │
    ├── every (2-8) ................ Apply every n cycles
    └── whenmod (3-8) .............. Apply when cycle % n
```

## 🔊 Sound Sample Categories

```
Sound Samples (38 total)
│
├── 🥁 DRUMS (11)
│   bd, sn, cp, hh, oh, ch, cy, rim, tom, clap, click
│
├── 🎸 BASS (6)
│   bass, bass0, bass1, bass2, bass3, jungbass
│
├── 🎹 SYNTHS (4)
│   superpiano, supersaw, supermandolin, supersquare
│
├── 🎧 BREAKS (4)
│   breaks125, breaks152, breaks165, amencutup
│
├── 🎛️ 808/909 (5)
│   808bd, 808sd, 808hh, 808oh, 808cy
│
└── 🎺 OTHER (8)
    cowbell, crash, hand, tabla, arpy, industrial, insect, jazz
```

## 📊 Code Generation Flow

```
PatternTree
    │
    ├─── Is Leaf? ──YES──> Generate Terminal
    │                       │
    │                       ├── sound ──> sound "bd"
    │                       ├── note ───> note "7"
    │                       └── silence > silence
    │
    └─── NO ──> Look up function in TidalGrammar.FUNCTIONS
                │
                ├── UNARY ──────────> op (child_pattern)
                │                     rev (sound "bd")
                │
                ├── BINARY_NUMERIC ─> op value $ child_pattern
                │                     fast 2.00 $ sound "sn"
                │
                ├── BINARY_INT ─────> op int $ child_pattern
                │                     chop 8 $ sound "arpy"
                │
                ├── PROBABILISTIC ──> op prob $ child_pattern
                │                     degradeBy 0.50 $ sound "hh"
                │
                ├── N_ARY ──────────> op [child1, child2, ...]
                │                     stack [sound "bd", sound "sn"]
                │
                └── CONDITIONAL ────> op n (transform) $ pattern
                                      every 4 (rev) $ sound "cp"
```

## 🔄 Pattern Generation Process

```
1. PatternTree.random(max_depth=4, method='grow')
   │
   ├─ Check depth and probability
   │  │
   │  ├─ Terminal? ──> _generate_terminal()
   │  │                ├─ sound: pick from TidalGrammar.SOUNDS
   │  │                ├─ note: random 0-11
   │  │                └─ silence
   │  │
   │  └─ Non-terminal? ──> _generate_nonterminal()
   │                        │
   │                        ├─ Pick random function signature
   │                        ├─ Generate parameter (if needed)
   │                        ├─ Generate children (recursive)
   │                        └─ Return PatternTree node
   │
   └─ Result: Complete tree with correct structure
```

## 💡 Example Transformations

```
Tree Representation          ->  TidalCycles Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

sound(bd)                    ->  sound "bd"

fast(2.0, sound(sn))         ->  fast 2.00 $ sound "sn"

rev(fast(2.0, sound(bd)))    ->  rev (fast 2.00 $ sound "bd")

stack(sound(bd),             ->  stack [sound "bd", sound "sn"]
      sound(sn))

every(4,                     ->  every 4 (rev (sound "arpy"))
      rev(sound(arpy)),                 $ sound "bd"
      sound(bd))

degradeBy(0.3,               ->  degradeBy 0.30
  striate(8,                      $ striate 8
    sound(808hh)))                  $ sound "808hh"
```

## 🛠️ Extension Template

### Adding a New Function

```python
# 1. Choose or create FunctionType
FunctionType.YOUR_TYPE

# 2. Add to TidalGrammar.FUNCTIONS
'yourfunction': FunctionSignature(
    name='yourfunction',
    func_type=FunctionType.YOUR_TYPE,
    param_generator=lambda: YOUR_PARAM_LOGIC,  # Optional
    min_children=MIN,
    max_children=MAX
),

# 3. (Optional) Add codegen rule in to_tidal() if new type
elif func_type == FunctionType.YOUR_TYPE:
    # Custom code generation logic
    return f"{tree.op} {custom_format}"

# 4. Done! Test with:
python examples/test_grammar.py
python examples/test_codegen_grammar.py
```

## 📈 Impact Metrics

```
Metric                  Before    After     Change
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Functions               7         25        +257%
Sound Samples           8         38        +375%
Function Types          Ad-hoc    6 formal  ✓
Code Lines (genome.py)  ~110      ~330      +200
Extensibility           Low       High      +++
Maintainability         Medium    High      ++
Type Safety             None      Full      ✓
```

## 🎯 Quick Start

```python
# 1. Generate a random pattern
from genetic_music.genome import PatternTree
pattern = PatternTree.random(max_depth=4)

# 2. Convert to TidalCycles code
from genetic_music.codegen import to_tidal
code = to_tidal(pattern)

# 3. Play in TidalCycles!
print(f"d1 $ {code}")
```

## 🧪 Test Commands

```bash
# Test grammar system
python examples/test_grammar.py

# Test code generation
python examples/test_codegen_grammar.py

# Test in your evolution code
python examples/basic_evolution.py
```

## 📚 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| `TIDAL_GRAMMAR.md` | Complete technical documentation | Developers |
| `QUICK_REFERENCE_GRAMMAR.md` | Quick lookup guide | All users |
| `GRAMMAR_IMPLEMENTATION_SUMMARY.md` | What was changed | Maintainers |
| `GRAMMAR_VISUAL_REFERENCE.md` | Visual diagrams (this file) | Visual learners |

## 🔗 External Resources

- 📖 [TidalCycles Documentation](https://tidalcycles.org/docs/)
- 🎵 [Control Functions Reference](https://userbase.tidalcycles.org/Control_Functions.html)
- 💬 [TidalCycles Community Forum](https://club.tidalcycles.org/)
- 🎼 [Mini-notation Syntax](https://userbase.tidalcycles.org/Mini_notation_syntax.html)

---

**Legend**:
- ✓ = Implemented
- ++ = Significant improvement
- +++ = Major improvement

