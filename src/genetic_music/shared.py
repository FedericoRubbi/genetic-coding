"""
Shared high/low interface: trigger a SuperDirt bus-controlled synth and
modify it live via control buses.
"""

import threading
import time
from typing import Optional, Callable

from .backend import Backend


class LayeredSound:
    """
    Abstraction for a single high-level trigger (SuperDirt \gpbus) that can be
    modified by low-level control buses during playback.
    """

    def __init__(
        self,
        backend: Backend,
        cutoff_bus: int = 100,
        res_bus: int = 101,
    ) -> None:
        self.backend = backend
        self.cutoff_bus = cutoff_bus
        self.res_bus = res_bus

    def _set_buses(self, cutoff_hz: float, res_norm: float) -> None:
        self.backend.set_control_bus(self.cutoff_bus, float(cutoff_hz))
        self.backend.set_control_bus(self.res_bus, float(res_norm))

    def play_high_only(
        self,
        freq_hz: float = 220.0,
        sustain_s: float = 1.5,
        amp: float = 0.9,
        pan: float = 0.0,
    ) -> None:
        # Set some defaults on buses; event will read them
        self._set_buses(cutoff_hz=800.0, res_norm=0.2)
        self.backend.send_superdirt_event(
            sample="gpbus",
            amp=float(amp),
            pan=float(pan),
            sustain=float(sustain_s),
            extra={
                "freq": float(freq_hz),
                "cutoffBus": int(self.cutoff_bus),
                "resBus": int(self.res_bus),
            },
        )

    def play_high_with_low_mod(
        self,
        freq_hz: float = 220.0,
        sustain_s: float = 1.5,
        amp: float = 0.9,
        pan: float = 0.0,
        cutoff_start: float = 400.0,
        cutoff_end: float = 4000.0,
        res_start: float = 0.2,
        res_end: float = 0.6,
        steps: int = 12,
        step_time_s: float = 0.08,
        async_mod: bool = False,
        on_step: Optional[Callable[[int, float, float], None]] = None,
    ) -> None:
        # Initialize buses to starting values
        self._set_buses(cutoff_start, res_start)

        # Trigger high-level event
        self.backend.send_superdirt_event(
            sample="gpbus",
            amp=float(amp),
            pan=float(pan),
            sustain=float(sustain_s),
            extra={
                "freq": float(freq_hz),
                "cutoffBus": int(self.cutoff_bus),
                "resBus": int(self.res_bus),
            },
        )

        def modulate() -> None:
            for i in range(steps):
                t = (i + 1) / float(steps)
                cutoff = cutoff_start + (cutoff_end - cutoff_start) * t
                res = res_start + (res_end - res_start) * t
                self._set_buses(cutoff, res)
                if on_step:
                    on_step(i + 1, cutoff, res)
                time.sleep(step_time_s)

        if async_mod:
            threading.Thread(target=modulate, daemon=True).start()
        else:
            modulate()


