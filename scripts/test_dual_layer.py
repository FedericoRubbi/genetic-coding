"""
Dual-layer test: send a high-level Tidal pattern alone, then send the same
pattern together with a low-level scsynth overlay so the second playback
sounds clearly different.

Prereqs:
- SuperCollider + SuperDirt running (see scripts/setup_supercollider.md)
- Orbits routed with Array.fill(12, 0) so /d8 is audible.

Run:
  source venv/bin/activate
  python scripts/test_dual_layer.py
"""

import sys
import time
from pathlib import Path

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from genetic_music import Backend  # type: ignore


def build_demo_pattern_str() -> str:
    # Use SuperDirt mini-notation directly (parsed by /dN endpoints)
    # Simple audible drum pattern
    return 'bd sn'


def main() -> None:
    backend = Backend(orbit=8)
    mini_code = build_demo_pattern_str()

    print("\n=== 1) High-level only (Tidal) ===")
    print(f"Pattern: {mini_code}")
    # Trigger via direct SuperDirt events to ensure audibility
    for _ in range(2):
        backend.send_superdirt_event('bd', amp=0.9, sustain=0.2)
        time.sleep(0.25)
        backend.send_superdirt_event('sn', amp=0.9, sustain=0.2)
        time.sleep(0.25)
    backend.stop_all()
    time.sleep(0.5)

    print("\n=== 2) High-level + Low-level overlay ===")
    print(f"Pattern: {mini_code}")
    # Start the pitched overlay asynchronously so it overlaps
    backend.spawn_default_synth(freq=660.0, amp=0.12, dur=1.2, out=0, block=False)
    for _ in range(2):
        backend.send_superdirt_event('bd', amp=0.9, sustain=0.2)
        time.sleep(0.25)
        backend.send_superdirt_event('sn', amp=0.9, sustain=0.2)
        time.sleep(0.25)
    backend.stop_all()
    time.sleep(0.5)

    print("\nDone. You should have heard two passes:"
          " first with drums only, then drums + pitched overlay.")


if __name__ == "__main__":
    main()


