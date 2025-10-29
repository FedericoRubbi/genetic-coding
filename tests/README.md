# Test Suite

This directory contains tests for the genetic music evolution system.

## Test Categories

### 1. Unit Tests (pytest)

These tests verify the correctness of individual components:

- **`test_genome.py`** - Tests genome structures (PatternTree, SynthTree, Genome)
- **`test_codegen.py`** - Tests code generation (Tree → Tidal/SuperCollider)

Run with pytest:
```bash
pytest tests/test_genome.py
pytest tests/test_codegen.py
# Or run all unit tests:
pytest tests/
```

### 2. Integration Tests (Manual)

These tests verify external system integration and require running services:

- **`test_supercollider.py`** - Tests SuperCollider server connectivity
- **`test_superdirt.py`** - Tests SuperDirt OSC communication and audio
- **`test_tidalcycles.py`** - Tests TidalCycles pattern generation

Run individually:
```bash
python tests/test_supercollider.py
python tests/test_superdirt.py
python tests/test_tidalcycles.py
```

## Quick Start

### Prerequisites for Integration Tests

1. **Install SuperCollider** (if not already installed):
   ```bash
   brew install --cask supercollider  # macOS
   ```

2. **Start SuperCollider and SuperDirt**:
   - Open SuperCollider IDE
   - Run the startup code from `scripts/setup_supercollider.md`
   - Verify you see: "SuperDirt started and ready!"

3. **Install Python dependencies**:
   ```bash
   pip install python-osc pytest
   ```

### Running Tests in Order

We recommend running tests in this order:

```bash
# 1. Unit tests (no external dependencies)
pytest tests/test_genome.py -v
pytest tests/test_codegen.py -v

# 2. SuperCollider server test
python tests/test_supercollider.py

# 3. SuperDirt audio test
python tests/test_superdirt.py

# 4. TidalCycles integration test
python tests/test_tidalcycles.py
```

## Test Details

### test_supercollider.py

Tests basic SuperCollider server functionality:
- OSC connection to server (port 57110)
- Server status requests
- Control bus operations
- Basic server commands

**Prerequisites:**
- SuperCollider is open
- Server is booted: `s.boot;`

**Expected output:**
```
✅ PASS: Server Connection
✅ PASS: Server Commands
✅ PASS: Control Bus
```

---

### test_superdirt.py

Tests SuperDirt sample playback and OSC communication:
- Connection to SuperDirt (port 57120)
- Basic drum samples (bd, sn, hh, cp)
- Multiple orbits
- Sample parameters (gain, speed, pan)
- Sample variants

**Prerequisites:**
- SuperCollider with SuperDirt running
- Samples loaded: `~dirt.loadSoundFiles;`
- All orbits audible: `~dirt.start(57120, Array.fill(12, 0));`

**Expected output:**
```
✅ PASS: SuperDirt Connection
✅ PASS: Basic Drum Samples
✅ PASS: Multiple Orbits
✅ PASS: Sample Parameters
✅ PASS: Sample Variants
```

You should **hear sounds** during this test!

---

### test_tidalcycles.py

Tests pattern generation and TidalCycles integration:
- Pattern code generation from genomes
- Different pattern structures
- Pattern playback via SuperDirt OSC
- Backend integration
- Tidal syntax validation

**Prerequisites:**
- SuperCollider with SuperDirt running
- genetic_music package importable

**Expected output:**
```
✅ PASS: Pattern Generation
✅ PASS: Pattern Structures
✅ PASS: Pattern Playback
✅ PASS: Backend Integration
✅ PASS: Syntax Validation
```

---

## SuperCollider Setup Commands

Quick reference for starting SuperDirt:

```supercollider
// 1. Start SuperDirt
(
s.options.numBuffers = 1024 * 256;
s.options.memSize = 8192 * 32;
s.waitForBoot {
    ~dirt = SuperDirt(2, s);
    ~dirt.loadSoundFiles;
    s.sync;
    ~dirt.start(57120, Array.fill(12, 0));
    "SuperDirt ready!".postln;
};
)

// 2. Optional: Enable OSC monitoring
OSCdef(\monitor, {|msg| msg.postln}, '/dirt/play');

// 3. Check orbit routing
~dirt.orbits.collect(_.outBus).postln;  // Should be all 0s

// 4. Test audio
{ SinOsc.ar(440) * 0.1 }.play;  // Stop with: s.freeAll;
```

## Troubleshooting

### "pythonosc not installed"
```bash
pip install python-osc
```

### "No module named 'genetic_music'"
```bash
# From project root:
pip install -e .
```

### "No sounds playing"
- Check SuperDirt is started: `~dirt.postln;` should show "a SuperDirt"
- Check orbits are audible: `~dirt.orbits.collect(_.outBus).postln;` should show `[0, 0, 0, ...]`
- Check volume in SuperCollider
- Test basic audio: `{ SinOsc.ar(440) * 0.1 }.play;`

### "Connection refused"
- Check SuperCollider is running
- Check server is booted: `s.boot;`
- Check port numbers:
  - SuperCollider server: 57110
  - SuperDirt: 57120

### "Samples not found"
```supercollider
// In SuperCollider:
Quarks.install("Dirt-Samples");
// Then restart SuperCollider and reload:
~dirt.loadSoundFiles;
```

## Continuous Integration (Future)

For automated testing:
- Unit tests can run in CI without external dependencies
- Integration tests require SuperCollider/SuperDirt and should be run manually or in a specialized CI environment with audio support

## Contributing

When adding new features:
1. Add unit tests to appropriate test files
2. Update integration tests if external interfaces change
3. Document any new prerequisites
4. Run all tests before submitting changes

