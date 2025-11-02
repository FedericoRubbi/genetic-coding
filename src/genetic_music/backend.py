"""
Communication backend for interacting with TidalCycles.

Handles OSC messaging for pattern playback.
"""

import time
import tempfile
from pathlib import Path
from typing import Optional
from pythonosc import udp_client


class Backend:
    """
    Backend for communicating with TidalCycles through SuperDirt.
    """
    
    def __init__(
        self,
        tidal_host: str = "127.0.0.1",
        tidal_port: int = 57120,  # SuperDirt listens here for /d1.. /d12
        orbit: int = 8  # Dedicated orbit for GP system
    ):
        """
        Initialize the backend.
        
        Args:
            tidal_host: TidalCycles host
            tidal_port: TidalCycles port (SuperDirt)
            orbit: Orbit number for GP system (0-11)
        """
        # Client for sending pattern messages to SuperDirt
        self.dirt_client = udp_client.SimpleUDPClient(tidal_host, tidal_port)
        self.orbit = orbit
        self.temp_dir = Path(tempfile.gettempdir()) / "genetic_music"
        self.temp_dir.mkdir(exist_ok=True)

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

    def cleanup(self) -> None:
        """Clean up temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

