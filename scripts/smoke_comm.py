"""
Smoke test: send a high-level Tidal pattern, then a low-level SuperCollider node.

Requirements:
- TidalCycles running and listening on port 6010
- SuperCollider with SuperDirt booted (port 57120)

Usage:
  source venv/bin/activate
  python scripts/smoke_comm.py
"""

import sys
import time
from pathlib import Path

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from genetic_music import Genome  # type: ignore
from genetic_music import Backend, to_tidal, to_supercollider  # type: ignore


def main() -> None:
    backend = Backend(orbit=8)

    # Generate a random genome (pattern + synth)
    genome = Genome.random(pattern_depth=3, synth_depth=3)

    print("\n--- Initial genome ---")
    tidal_code = to_tidal(genome.pattern_tree)
    sc_code = to_supercollider(genome.synth_tree, synth_name="evolved_smoke")
    print(f"Tidal: {tidal_code}")
    print(f"SC SynthDef (preview): {sc_code[:120]}...")

    # High-level: send pattern to Tidal (timing/structure)
    print("\n[High-level] Sending Tidal pattern to /d8...")
    backend.send_pattern(tidal_code)
    time.sleep(1.0)

    # Low-level: spawn a simple default synth node on scsynth (timbre)
    print("[Low-level] Spawning \\default node on scsynth...")
    backend.spawn_default_synth(freq=440.0, amp=0.15, dur=1.0, out=0)

    # Apply a simple random mutation and resend
    print("\n--- Applying random mutation ---")
    mutated = genome.mutate(rate=1.0)
    tidal_code_2 = to_tidal(mutated.pattern_tree)
    sc_code_2 = to_supercollider(mutated.synth_tree, synth_name="evolved_smoke2")

    print(f"Tidal (mutated): {tidal_code_2}")
    print(f"SC SynthDef (mutated, preview): {sc_code_2[:120]}...")

    print("\n[High-level] Sending mutated Tidal pattern...")
    backend.send_pattern(tidal_code_2)
    time.sleep(1.0)

    print("[Low-level] Spawning another \\default node...")
    backend.spawn_default_synth(freq=660.0, amp=0.12, dur=1.0, out=0)

    print("\nDone. If both layers sounded without errors, communication is conflict-free.")


if __name__ == "__main__":
    main()


