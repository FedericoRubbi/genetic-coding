"""
Shared high/low interface: trigger a SuperDirt bus-controlled synth and
modify it live via control buses.
"""

import threading
import time
from typing import Optional, Callable, List, Dict

from .backend import Backend
from .genome import Genome
from .codegen import to_supercollider, extract_synth_params


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
        synth_name: str = "gpbus",
    ) -> None:
        self.backend = backend
        self.cutoff_bus = cutoff_bus
        self.res_bus = res_bus
        self.synth_name = synth_name

    def _set_buses(self, cutoff_hz: float, res_norm: float) -> None:
        self.backend.set_control_bus(self.cutoff_bus, float(cutoff_hz))
        self.backend.set_control_bus(self.res_bus, float(res_norm))

    def play_high_only(
        self,
        freq_hz: float = 220.0,
        sustain_s: float = 1.5,
        amp: float = 0.9,
        pan: float = 0.0,
        synth_params: Optional[Dict[str, float]] = None,
    ) -> None:
        # Set some defaults on buses; event will read them
        self._set_buses(cutoff_hz=800.0, res_norm=0.2)
        extra = {
            "freq": float(freq_hz),
            "cutoffBus": int(self.cutoff_bus),
            "resBus": int(self.res_bus),
        }
        if synth_params:
            extra.update(synth_params)
        
        self.backend.send_superdirt_event(
            sample=self.synth_name,
            amp=float(amp),
            pan=float(pan),
            sustain=float(sustain_s),
            extra=extra,
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
        synth_params: Optional[Dict[str, float]] = None,
    ) -> None:
        # Initialize buses to starting values
        self._set_buses(cutoff_start, res_start)

        # Trigger high-level event
        extra = {
            "freq": float(freq_hz),
            "cutoffBus": int(self.cutoff_bus),
            "resBus": int(self.res_bus),
        }
        if synth_params:
            extra.update(synth_params)
        
        self.backend.send_superdirt_event(
            sample=self.synth_name,
            amp=float(amp),
            pan=float(pan),
            sustain=float(sustain_s),
            extra=extra,
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
    
    def play_evolved(
        self,
        genome: Genome,
        freq_hz: float = 220.0,
        sustain_s: float = 1.5,
        amp: float = 0.9,
        pan: float = 0.0,
        enable_modulation: bool = True,
        cutoff_start: float = 500.0,
        cutoff_end: float = 3500.0,
        res_start: float = 0.2,
        res_end: float = 0.6,
        steps: int = 12,
    ) -> None:
        """
        Play a genome's evolved sound.
        
        Args:
            genome: Genome containing evolved synth_tree
            freq_hz: Note frequency
            sustain_s: Note duration
            amp: Amplitude
            pan: Pan position
            enable_modulation: If True, modulate via control buses
            cutoff_start: Starting cutoff for modulation
            cutoff_end: Ending cutoff for modulation
            res_start: Starting resonance for modulation
            res_end: Ending resonance for modulation
            steps: Number of modulation steps
        """
        # Extract evolved parameters from genome
        synth_params = extract_synth_params(genome.synth_tree)
        
        if enable_modulation:
            step_time = max(0.02, sustain_s / steps)
            self.play_high_with_low_mod(
                freq_hz=freq_hz,
                sustain_s=sustain_s,
                amp=amp,
                pan=pan,
                cutoff_start=cutoff_start,
                cutoff_end=cutoff_end,
                res_start=res_start,
                res_end=res_end,
                steps=steps,
                step_time_s=step_time,
                synth_params=synth_params,
            )
        else:
            self.play_high_only(
                freq_hz=freq_hz,
                sustain_s=sustain_s,
                amp=amp,
                pan=pan,
                synth_params=synth_params,
            )


class GenomePlayer:
    """Manages loading and playing evolved genomes."""
    
    def __init__(self, backend: Backend, orbit: int = 8):
        self.backend = backend
        self.orbit = orbit
        self.loaded_synthdefs: Dict[str, int] = {}  # synth_name -> genome_id
    
    def load_genome_synth(self, genome: Genome, genome_id: int) -> Optional[str]:
        """
        Compile and load genome's SynthTree.
        
        Args:
            genome: Genome to load
            genome_id: Unique identifier for this genome
        
        Returns:
            The loaded SynthDef name, or None if loading failed
        """
        synth_name = f"evolved_{genome_id}"
        synthdef_code = to_supercollider(genome.synth_tree, synth_name)
        success = self.backend.load_synthdef(synthdef_code, synth_name)
        if success:
            self.loaded_synthdefs[synth_name] = genome_id
        return synth_name if success else None
    
    def play_genome_phrase(
        self,
        genome: Genome,
        genome_id: int,
        note_freqs: List[float],
        sustain: float = 1.0,
        amp: float = 0.9,
        enable_modulation: bool = True,
    ) -> None:
        """
        Load genome synth and play phrase with its evolved sound.
        
        Args:
            genome: Genome to play
            genome_id: Unique identifier
            note_freqs: List of frequencies to play
            sustain: Duration of each note
            amp: Amplitude
            enable_modulation: Enable control bus modulation
        """
        # Load the genome's synth
        synth_name = self.load_genome_synth(genome, genome_id)
        if not synth_name:
            print(f"[GenomePlayer] Failed to load synth for genome {genome_id}")
            return
        
        # Create LayeredSound with evolved synth
        layer = LayeredSound(
            self.backend,
            synth_name=synth_name,
            cutoff_bus=100,
            res_bus=101,
        )
        
        # Play each note
        for freq in note_freqs:
            layer.play_evolved(
                genome=genome,
                freq_hz=freq,
                sustain_s=sustain,
                amp=amp,
                enable_modulation=enable_modulation,
            )
            time.sleep(sustain + 0.15)  # Note duration plus small gap


