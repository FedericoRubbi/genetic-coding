// Bus-controlled SuperDirt synth for shared high/low interface
// Load this in SuperCollider before running the shared-interface test.

(
~dirt.soundLibrary.addSynth(\gpbus, { |out=0, sustain=1.0, amp=0.9, pan=0, freq=220,
    cutoffBus=0, resBus=0|
    var cutoff = In.kr(cutoffBus, 1).clip(50, 12000);
    var res = In.kr(resBus, 1).linlin(0, 1, 0.05, 0.95);
    var env = EnvGen.kr(Env.linen(0.01, sustain, 0.1), doneAction: 2);
    var sig = RLPF.ar(Saw.ar(freq), cutoff, res);
    sig = Pan2.ar(sig, pan);
    Out.ar(out, sig * amp * env);
});
)

// Usage example (manual):
// ~cutBus = Bus.control(s, 1);
// ~resBus = Bus.control(s, 1);
// ~cutBus.set(400);
// ~resBus.set(0.2);
// ~dirt.orbits[0].play2((s: \gpbus, sustain: 1.5, freq: 220, cutoffBus: ~cutBus.index, resBus: ~resBus.index));
// // live change
// ~cutBus.set(1200);

