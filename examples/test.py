"""
Minimal example of pattern evolution using structural fitness.
Shows basic pattern generation and evolution with audio playback.
"""

import os
from pathlib import Path
from genetic_music.backend import Backend
import time


def main():
    # Initialize backend for audio playback
    # You need to set the path to your BootTidal.hs file
    BOOT_TIDAL = os.path.expanduser("/Users/federicorubbi/.cabal/share/aarch64-osx-ghc-9.12.2-ea3d/tidal-1.10.1/BootTidal.hs")
    if not os.path.exists(BOOT_TIDAL):
        print("Please set the correct path to your BootTidal.hs file!")
        return

    backend = Backend(
        boot_tidal_path=BOOT_TIDAL,
        orbit=8,    # SuperDirt orbit to render on
        stream=12   # dedicated Tidal stream (d12) for our patterns
    )

    backend.tidal.eval(f'd{backend.stream} $ s "bd sd cp hh*2" # orbit {backend.orbit} # gain 1')

    time.sleep(2.0)
    backend.tidal.silence_stream(backend.stream)

    backend.play_tidal_code(
        rhs_pattern_expr='s "bd sd cp hh*2" # gain 1',
        duration=4.0,
        output_path=Path("/Users/federicorubbi/Documents/unitn/bio-inspired-artificial-intelligence/genetic-coding/data/outputs/minimal_evolution/best_pattern.wav"),
        playback_after=True
    )
    # Clean up
    backend.close()


if __name__ == "__main__":
    main()