"""
Communication backend for interacting with TidalCycles and SuperCollider.

Handles OSC messaging, audio recording, and system coordination.
"""

import time
import threading
import tempfile
from pathlib import Path
from typing import Optional
from pythonosc import udp_client, osc_message_builder, osc_bundle_builder


class Backend:
    """
    Backend for communicating with TidalCycles and SuperDirt/SuperCollider.
    """
    
    def __init__(
        self,
        sc_host: str = "127.0.0.1",
        sc_port: int = 57110,  # scsynth command port (default)
        tidal_host: str = "127.0.0.1",
        tidal_port: int = 57120,  # SuperDirt listens here for /d1.. /d12
        orbit: int = 8  # Dedicated orbit for GP system
    ):
        """
        Initialize the backend.
        
        Args:
            sc_host: SuperCollider/SuperDirt host
            sc_port: SuperCollider/SuperDirt port
            tidal_host: TidalCycles host
            tidal_port: TidalCycles port
            orbit: Orbit number for GP system (0-11)
        """
        # scsynth client: use for /s_new, /n_set, /c_set, /n_free, etc.
        self.sc_client = udp_client.SimpleUDPClient(sc_host, sc_port)
        # SuperDirt client: use for /d1.. /d12 pattern messages (mini-notation strings)
        self.dirt_client = udp_client.SimpleUDPClient(tidal_host, tidal_port)
        self.orbit = orbit
        self.temp_dir = Path(tempfile.gettempdir()) / "genetic_music"
        self.temp_dir.mkdir(exist_ok=True)
    
    def send_synthdef(self, synthdef_code: str) -> None:
        """
        Send a SynthDef to SuperCollider.
        
        Args:
            synthdef_code: SuperCollider SynthDef code
        """
        # TODO: Implement SynthDef sending
        # Options:
        # 1. Send via OSC /d_recv with compiled bytecode
        # 2. Write to file and load via /d_load
        # 3. Use sclang to compile and send
        
        # For now, we'll assume a running SuperCollider instance
        # that can receive code via a custom OSC endpoint
        # or through a file-based mechanism
        
        print(f"[Backend] SynthDef sent (stub):\n{synthdef_code[:100]}...")
    
    def send_pattern(self, pattern_code: str) -> None:
        """
        Send a pattern to TidalCycles.
        
        Args:
            pattern_code: Tidal pattern code
        """
        # Send pattern to SuperDirt orbit
        # Format: /d<orbit> <pattern_string>
        orbit_addr = f"/d{self.orbit}"
        
        try:
            self.dirt_client.send_message(orbit_addr, pattern_code)
            print(f"[Backend] Pattern sent to SuperDirt orbit {self.orbit}: {pattern_code[:50]}...")
        except Exception as e:
            print(f"[Backend] Error sending pattern: {e}")
    
    def play_pattern(
        self,
        pattern_code: str,
        duration: float = 2.0,
        speed: float = 1.0,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Play a pattern and record the audio output.
        
        Args:
            pattern_code: Tidal pattern code
            duration: Recording duration in seconds
            speed: Playback speed multiplier (>1 = faster)
            output_path: Path to save audio file (optional)
        
        Returns:
            Path to recorded audio file
        """
        if output_path is None:
            output_path = self.temp_dir / f"pattern_{int(time.time())}.wav"
        
        # TODO: Implement actual recording
        # 1. Send pattern to Tidal
        # 2. Start recording in SuperCollider
        # 3. Wait for duration / speed
        # 4. Stop recording
        # 5. Return audio file path
        
        self.send_pattern(pattern_code)
        
        # Simulate recording
        time.sleep(duration / speed)
        
        print(f"[Backend] Audio recorded to {output_path} (stub)")
        return output_path
    
    def set_control_bus(self, bus: int, value: float) -> None:
        """
        Set a control bus value.
        
        Args:
            bus: Control bus number
            value: Value to set
        """
        self.sc_client.send_message("/c_set", [bus, value])
    
    def override_synth_param(self, node_id: int, param: str, value: float) -> None:
        """
        Override a synth parameter.
        
        Args:
            node_id: Synth node ID
            param: Parameter name
            value: Parameter value
        """
        self.sc_client.send_message("/n_set", [node_id, param, value])
    
    def stop_all(self) -> None:
        """Stop all playback."""
        # Silence the orbit
        self.send_pattern("silence")
        
        # Optionally send /g_freeAll to the orbit's group
        # (requires knowing the group ID structure)
    
    def play2(self, params: dict) -> None:
        """Send a direct SuperDirt event via /play2 with key-value pairs.
        Example params: { 's': 'bd', 'amp': 0.9, 'orbit': 8, 'sustain': 0.2 }
        """
        try:
            flat = []
            for k, v in params.items():
                flat.extend([str(k), v])
            self.dirt_client.send_message("/play2", flat)
        except Exception as e:
            print(f"[Backend] Error sending /play2: {e}")
    
    def send_superdirt_event(
        self,
        sample: str,
        amp: float = 0.9,
        pan: float = 0.5,
        speed: float = 1.0,
        sustain: float = 0.2,
        orbit: Optional[int] = None,
        extra: Optional[dict] = None,
    ) -> None:
        """Convenience wrapper to trigger a SuperDirt sample once."""
        params = {
            's': sample,
            'amp': float(amp),
            'pan': float(pan),
            'speed': float(speed),
            'sustain': float(sustain),
            'orbit': int(self.orbit if orbit is None else orbit),
        }
        if extra:
            params.update(extra)
        self.play2(params)
    
    def ping_sc(self) -> None:
        """Send a status request to SuperCollider (no reply expected here)."""
        try:
            self.sc_client.send_message("/status", [])
            print("[Backend] Sent /status to SuperCollider")
        except Exception as e:
            print(f"[Backend] Error pinging SC: {e}")
    
    def spawn_default_synth(self, freq: float = 440.0, amp: float = 0.2, dur: float = 1.0, out: int = 0, node_id: Optional[int] = None, block: bool = True) -> int:
        """
        Spawn a simple \default synth node directly on scsynth to test coexistence with SuperDirt.
        This is independent of Tidal/SuperDirt nodes and is safe to run concurrently.
        
        Args:
            freq: Frequency in Hz
            amp: Amplitude (0..1)
            dur: Duration in seconds before freeing the node
            out: Output bus (0 = main stereo)
            node_id: Optional explicit node id
        
        Returns:
            The node id used for the synth
        """
        nid = node_id or int(time.time() * 1000) % 100000000
        try:
            # /s_new name nodeID addAction targetID ...args
            # addAction 1 = add to head of group 1 (default group)
            self.sc_client.send_message("/s_new", ["default", nid, 1, 1, "freq", float(freq), "amp", float(amp), "out", int(out)])
            print(f"[Backend] Spawned \\default node {nid} (freq={freq}, amp={amp})")
            
            def free_after_delay():
                try:
                    time.sleep(max(0.0, dur))
                    self.sc_client.send_message("/n_free", [nid])
                    print(f"[Backend] Freed node {nid}")
                except Exception as e:
                    print(f"[Backend] Error freeing node {nid}: {e}")
            
            if block:
                free_after_delay()
            else:
                threading.Thread(target=free_after_delay, daemon=True).start()
        except Exception as e:
            print(f"[Backend] Error spawning default synth: {e}")
        return nid
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

