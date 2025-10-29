## Project Recap: Genetic Coding for Music

This document summarizes the current architecture, representations, and the SuperCollider/SuperDirt integration used by the project. It consolidates key points from the codebase and docs, and captures the shared-layer fix that restored audio.

### High-level view

- **Evolution loop**: `src/genetic_music/evolve.py` orchestrates population init → evaluation → selection → variation.
- **Genome**: `src/genetic_music/genome.py` models individuals with two trees:
  - **PatternTree** (high-level, Tidal-like) for musical structure and scheduling.
  - **SynthTree** (low-level, SuperCollider) for synthesis graphs.
- **CodeGen**: `src/genetic_music/codegen.py` turns trees into executable text:
  - `to_tidal(tree)` → Tidal-like pattern string.
  - `to_supercollider(tree)` → SuperCollider `SynthDef` code.
- **Backend**: `src/genetic_music/backend.py` handles OSC I/O to Tidal/SuperDirt and SC, plus convenience helpers for events and buses.
- **Fitness**: `src/genetic_music/fitness.py` evaluates recorded audio using heuristic and/or embedding-based criteria.

## High-level representation (PatternTree)

### What it is

- A grammar-driven symbolic tree that represents TidalCycles-style pattern transformations and combinators.
- Formalized via `TidalGrammar` and `FunctionSignature` with six function types: UNARY, BINARY_NUMERIC, BINARY_INT, N_ARY, CONDITIONAL, PROBABILISTIC.
- Terminals include `sound`, `note`, and `silence`; `sound` draws from a curated list of SuperDirt samples.

### Expressiveness

- Covers a useful subset of Tidal concepts:
  - **Transformers**: `rev`, `palindrome`, `brak`, `degrade`, `shuffle`, `scramble`.
  - **Time/density**: `fast`, `slow`, `density`, `sparsity`, `hurry`.
  - **Structure**: `stack`, `cat`, `fastcat`, `slowcat`, `append`, `overlay`.
  - **Conditional/probabilistic**: `every`, `whenmod`, `degradeBy`, `sometimesBy`.
- Designed to be extensible by adding new `FunctionSignature`s and corresponding generation rules.

### Generation and code emission

- `PatternTree.random()` uses the grammar to produce syntactically valid, musically diverse trees with either grow or full strategies.
- `to_tidal()` walks the tree and emits a pattern string following the function-type rules (e.g., binary numeric functions emit `op value $ pattern`).

Notes/limits:
- Complex Tidal features (full mini-notation sequences, effect parameter chains, arithmetic patterns) are noted for future extension.

## Low-level representation (SynthTree)

### What it is

- A synthesis graph built from a small, practical vocabulary of UGens: oscillators (`SinOsc`, `Saw`, `Pulse`, `WhiteNoise`), filters (`LPF`, `HPF`, `BPF`, `RLPF`), and a few effects (`Mix`, `Pan2`, `FreeVerb`).
- Trees are generated randomly with depth controls; leaves are oscillators, non-leaves are filters/effects that compose child subgraphs.

### Code emission

- `to_supercollider()` converts a `SynthTree` into a full `SynthDef` with a simple ADSR envelope and `Out.ar`. This is used when evolving/compiling bespoke synths.

## Shared high/low layer integration (bus-controlled SuperDirt synth)

### Goal

- Enable a single high-level trigger (SuperDirt event) to be continuously modulated by low-level parameters (control buses) during its sustain window.

### Working solution in SuperCollider

- Define a SuperDirt-compatible `SynthDef` named `\gpbus` that reads control values from shared buses for cutoff and resonance.
- Register it with the SuperDirt sound library under the same name, so it can be triggered like a normal sample/instrument in events.

Essential snippet (as evaluated):

```supercollider
(
~gpCutBus = ~gpCutBus ?? { Bus.control(s, 1) };
~gpResBus = ~gpResBus ?? { Bus.control(s, 1) };

SynthDef(\gpbus, { |out=0, pan=0, freq=220, amp=0.9, sustain=1,
    cutoffBus = (~gpCutBus.index), resBus = (~gpResBus.index)|
    var cutoff = In.kr(cutoffBus, 1).clip(50, 12000);
    var res    = In.kr(resBus, 1).linlin(0, 1, 0.05, 0.95);
    var env = EnvGen.kr(Env.linen(0.01, sustain, 0.1), doneAction: 2);
    var sig = RLPF.ar(Saw.ar(freq), cutoff, res) * env;
    OffsetOut.ar(out, DirtPan.ar(sig, ~dirt.numChannels, pan) * amp);
}).add;

~dirt.soundLibrary.addSynth(\gpbus, (instrument: \gpbus));
)
```

Why this works:
- `DirtPan` runs inside a `SynthDef` build (no `\span.ir` error), and the synth reads `cutoffBus`/`resBus` indices supplied at event time.
- Defaults bind to shared buses so Python can modulate them live with `/c_set`.

### Python-side control flow

- `src/genetic_music/shared.py` provides `LayeredSound` with two use cases:
  - `play_high_only(...)`: triggers `\gpbus` with initial bus values (high-level only).
  - `play_high_with_low_mod(...)`: triggers `\gpbus`, then steps `cutoffBus`/`resBus` over time for a live sweep (adds low-level modulation).
- Under the hood this uses `Backend`:
  - `send_superdirt_event(...)/play2` to fire a SuperDirt event for `s: "gpbus"` with `freq`, `sustain`, and bus indices in the event.
  - `set_control_bus(bus, value)` to modulate buses via `/c_set` while the event is sounding.

## Communication with SuperCollider and SuperDirt

### OSC endpoints in use

- Pattern playback:
  - `Backend.send_pattern()` → sends a pattern string to `/d<orbit>` on the SuperDirt port (project default orbit is `8`).
- Direct SuperDirt event:
  - `Backend.play2(params)` → sends `/play2` with key/value pairs (e.g., `{ 's': 'gpbus', 'sustain': 1.5, 'freq': 220, 'orbit': 8 }`).
- Low-level modulation:
  - `Backend.set_control_bus(bus, value)` → `/c_set` to update shared control buses while the synth is active.
- Node parameter override (optional):
  - `Backend.override_synth_param(node_id, param, value)` → `/n_set` on specific synth nodes.

Notes:
- The backend currently treats the SuperDirt port (`57120`) as the target for `/d<orbit>` and `/play2`. This works well for the shared-layer approach and simple pattern strings.

## Expressiveness and current scope

### High-level (PatternTree)

- Good coverage of core transformations, combinators, and conditional/probabilistic logic.
- Balanced random generation enables diverse rhythmic/structural results while remaining valid.
- Future growth: effect parameters, mini-notation sequences, arithmetic patterns, function weighting.

### Low-level (SynthTree and shared layer)

- `SynthTree` can construct varied subtractive/AM-like chains with basic effects; envelope and output are provided in codegen.
- The shared-layer `\gpbus` provides real-time macro control (cutoff/res) that’s ideal for genetic experiments blending structure and timbre.
- Future growth: richer UGen set, modulation sources (LFOs/envs), more mapped buses.

## Recent issue and resolution (no sound / addIr error)

- Symptom: SuperCollider error `Message 'addIr' not understood` coming from `DirtPan` controls (e.g., `\span.ir(1)`), and silence.
- Root cause: calling `DirtPan` outside a `SynthDef` build due to how the `addSynth` function was written; SuperDirt attempted to create NamedControls without a builder context.
- Fix: define a proper `SynthDef(\gpbus, ...)` that uses `DirtPan` inside the graph and register it with `~dirt.soundLibrary.addSynth(\gpbus, (instrument: \gpbus))`. Use shared control buses for modulation.
- Extra: remove calls to methods not present in your SuperDirt version (e.g., `removeSynth`), and prefer `cutoffBus`/`resBus` defaults bound to the shared buses.

## How this ties into evolution and fitness

- For evolved synths: use `to_supercollider()` to compile per-genome `SynthDef`s and upload them (future: implement `/d_recv` or `/d_load`).
- For pattern evolution: use `to_tidal()` to emit pattern strings and `send_pattern()` or `/play2` to render via SuperDirt.
- Fitness evaluates recorded audio (currently mocked in `Backend.play_pattern`; ready to connect to SC recording) with heuristic/embedding pipelines in `fitness.py`.

## Practical checklist

- Ensure SuperDirt is running and listening on the expected port.
- Evaluate the `\gpbus` SC snippet once per session after SuperDirt is ready.
- In Python, use `LayeredSound` to trigger the high-level event and modulate the buses for the shared-layer test.
- Silence orbit with `Backend.stop_all()` when needed.

## Pointers

- High-level grammar: `docs/TIDAL_GRAMMAR.md`, `docs/QUICK_REFERENCE_GRAMMAR.md`, `docs/GRAMMAR_IMPLEMENTATION_SUMMARY.md`.
- Architecture overview and flows: `docs/architecture.md`.
- Core modules: `src/genetic_music/genome.py`, `src/genetic_music/codegen.py`, `src/genetic_music/backend.py`, `src/genetic_music/shared.py`.


