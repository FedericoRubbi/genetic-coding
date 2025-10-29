"""
Shared interface test:
1) Play one high-level \gpbus sound (unmodified)
2) Play the same \gpbus sound and live-modify it via control buses

Before running:
- In SuperCollider, evaluate scripts/sc/gpbus.scd (your corrected version)
- Ensure SuperDirt is running and orbits route to main out

Run:
  source venv/bin/activate
  python scripts/test_shared_interface.py
"""

import sys
import time
from pathlib import Path

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from genetic_music import Backend  # type: ignore
from genetic_music.shared import LayeredSound  # type: ignore


def main() -> None:
    backend = Backend(orbit=8)
    # Choose fixed control buses; they don't need sclang allocation
    cutoff_bus = 100
    res_bus = 101
    layered = LayeredSound(backend, cutoff_bus=cutoff_bus, res_bus=res_bus)

    print("\n=== Pass 1: High-level only (gpbus, unmodified) ===")
    layered.play_high_only(freq_hz=220.0, sustain_s=1.5, amp=0.9)
    time.sleep(2.0)
    backend.stop_all()
    time.sleep(0.3)

    print("\n=== Pass 2: High-level + Low-level (live bus modulation) ===")
    layered.play_high_with_low_mod(
        freq_hz=220.0,
        sustain_s=1.8,
        amp=0.9,
        cutoff_start=400.0,
        cutoff_end=4000.0,
        res_start=0.1,
        res_end=0.7,
        steps=12,
        step_time_s=0.08,
        async_mod=False,
    )
    backend.stop_all()
    time.sleep(0.3)

    print("\nDone. You should hear a single tone first, then the same tone being filter-swept.")


if __name__ == "__main__":
    main()


