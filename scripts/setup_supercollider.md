# SuperCollider Setup for Genetic Music

This guide explains how to set up SuperCollider and SuperDirt for use with the genetic music system.

## Prerequisites

- SuperCollider installed
- SuperDirt Quark installed

## Installation

### 1. Install SuperCollider

Download and install SuperCollider from: https://supercollider.github.io/

### 2. Install SuperDirt

Open SuperCollider and run:

```supercollider
Quarks.install("SuperDirt");
```

### 3. Basic SuperDirt Setup

Create a startup file with the following code:

```supercollider
(
s.options.numBuffers = 1024 * 256;
s.options.memSize = 8192 * 32;
s.options.numWireBufs = 128;
s.options.maxNodes = 1024 * 32;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 2;

s.waitForBoot {
    ~dirt = SuperDirt(2, s);
    ~dirt.loadSoundFiles;
    s.sync;
    ~dirt.start(57120, Array.fill(12, 0)); // All orbits to main output (bus 0)
    "SuperDirt started".postln;
};
)
```

### 4. Orbit Configuration

The genetic programming system uses orbit 8 by default to avoid conflicts with live coding in orbits 0-7.

**Important**: All orbits should be routed to the main output (bus 0) to be audible:
- `Array.fill(12, 0)` routes all 12 orbits to bus 0 (speakers)
- To mute a specific orbit, route it to a different bus number (e.g., `[0, 0, 8, ...]` mutes orbit 2)

Check orbit routing:
```supercollider
~dirt.orbits.collect(_.outBus).postln;  // Should show [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

### 5. Enable Audio Recording

To record audio from SuperCollider:

```supercollider
// Start recording
s.record;

// Stop recording
s.stopRecording;
```

Or use the Recorder class for more control:

```supercollider
(
r = Recorder(s);
r.record(path: "~/output.wav", numChannels: 2);
)

// Stop recording
r.stopRecording;
```

## Testing the Setup

### Test OSC Communication

```supercollider
// Listen for OSC messages
OSCFunc.trace(true);

// Stop tracing
OSCFunc.trace(false);
```

### Test Pattern Playback

From Python, you can send:

```python
from genetic_music import Backend

backend = Backend()
backend.send_pattern('sound "bd sn cp hh"')
### Load the Bus-Controlled Synth (Shared Interface)

Evaluate this file in SuperCollider:

```
scripts/sc/gpbus.scd
```

This registers a `\gpbus` synth in SuperDirt that reads filter cutoff and resonance from control buses.
Then run the shared-interface test:

```bash
python scripts/test_shared_interface.py
```
```

## Troubleshooting

### Port Conflicts

If port 57120 is in use, you can change SuperDirt's port:

```supercollider
~dirt.start(57121, Array.fill(12, 0));
```

And update your Python configuration accordingly.

### Audio Output Issues

Check your audio device:

```supercollider
ServerOptions.devices; // List available devices
s.options.device = "Your Device Name";
```

## Advanced: Non-Realtime Rendering

For deterministic offline rendering:

```supercollider
(
var score = Score([
    [0.0, [\d_recv, /* SynthDef bytes */]],
    [0.5, [\s_new, \synth, 1000, 0, 1]],
    [2.0, [\c_set, 0, 0]],
]);

score.recordNRT(
    outputFilePath: "~/output.wav",
    sampleRate: 44100,
    headerFormat: "wav",
    sampleFormat: "int16",
    options: ServerOptions.new.numOutputBusChannels_(2)
);
)
```

## Resources

- SuperCollider documentation: https://doc.sccode.org/
- SuperDirt repository: https://github.com/musikinformatik/SuperDirt
- TidalCycles documentation: https://tidalcycles.org/

