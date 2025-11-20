"""
Backend for driving TidalCycles via GHCi and recording audio via SuperCollider.
- Requires: Tidal installed, a valid BootTidal.hs path, SuperDirt running.
"""

import os
import time
import shlex
import platform
import subprocess
from pathlib import Path
from typing import Optional
from pythonosc import udp_client


class TidalGhci:
    """
    Launches a GHCi process, loads BootTidal.hs, and lets you eval Tidal code.
    """
    def __init__(self, boot_tidal_path: str, ghci_cmd: str = "ghci"):
        self.boot_tidal_path = Path(boot_tidal_path)
        if not self.boot_tidal_path.exists():
            raise FileNotFoundError(f"BootTidal.hs not found: {boot_tidal_path}")

        # Start ghci with a clean prompt (no user .ghci), line-buffered I/O
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

        self.proc = subprocess.Popen(
            [ghci_cmd, "-ignore-dot-ghci"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )

        # Load BootTidal.hs (standard way editors do)
        self._write(f':script {self._quote(self.boot_tidal_path)}')
        # Optional: set a distinct prompt so we can detect readiness
        self._write(':set prompt "tidal> "')
        self._wait_for("tidal>")

    def _quote(self, p: Path) -> str:
        return shlex.quote(str(p))

    def _write(self, line: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_available(self, timeout: float = 0.2) -> str:
        """Best-effort, non-blocking-ish read to drain output."""
        out = []
        end = time.time() + timeout
        assert self.proc.stdout is not None
        while time.time() < end and not self.proc.poll():
            chunk = self.proc.stdout.read(1)
            if not chunk:
                break
            out.append(chunk)
            if self.proc.stdout.peek(1):  # type: ignore[attr-defined]
                # On some platforms .peek doesn't exist; harmless if it fails
                continue
        return "".join(out)

    def _wait_for(self, token: str, timeout: float = 10.0):
        """Wait until GHCi prints a token (e.g., the prompt)."""
        assert self.proc.stdout is not None
        start = time.time()
        buf = ""
        while time.time() - start < timeout:
            c = self.proc.stdout.read(1)
            if not c:
                time.sleep(0.01)
                continue
            buf += c
            if token in buf:
                return
        # If prompt not seen, we'll still continue; print what we saw.
        print("[TidalGhci] Wait timed out. Output so far:\n", buf)

    def eval(self, code: str):
        """
        Evaluate a single Tidal line. Example:
          tidal.eval('d12 $ s "bd sd" # orbit 8')
        """
        self._write(code)

    def silence_stream(self, stream: int):
        self.eval(f"d{stream} silence")

    def hush(self):
        self.eval("hush")

    def close(self):
        try:
            self._write(":quit")
        except Exception:
            pass
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class Backend:
    """
    High-level API: record a generated Tidal pattern to a .wav and (optionally) play it back.
    - Plays via Tidal (GHCi), records via SC (OSC).
    """
    def __init__(
        self,
        boot_tidal_path: str,
        ghci_cmd: str = "ghci",
        sc_host: str = "127.0.0.1",
        sc_port: int = 57120,
        orbit: int = 8,     # SuperDirt orbit to render on
        stream: int = 12,   # Tidal stream d1..d16 (choose a reserved one)
    ):
        self.tidal = TidalGhci(boot_tidal_path=boot_tidal_path, ghci_cmd=ghci_cmd)
        self.osc = udp_client.SimpleUDPClient(sc_host, sc_port)
        self.orbit = int(orbit)
        self.stream = int(stream)
        self.out_dir = Path("data/outputs")

    # ---- SuperCollider recording helpers ----
    def _sc_record_start(self, path: Path, duration: float):
        self.osc.send_message("/gp/startRecord", [str(path), float(duration)])

    def _sc_record_stop(self):
        self.osc.send_message("/gp/stopRecord", [])

    # ---- Public API ----
    def play_tidal_code(
        self,
        rhs_pattern_expr: str,
        duration: float = 8.0,
        output_path: Optional[Path] = None,
        playback_after: bool = False,
    ) -> Path:
        """
        Record a Tidal pattern constructed as a RIGHT-HAND-SIDE expression.
        Example rhs:  s "bd sd [bd sn]" # speed 1.1

        We send:      d{stream} $ (rhs) # orbit {orbit}

        Returns: Path to the recorded WAV.
        """
        if output_path is None:
            output_path = self.out_dir / f"best_pattern_{int(time.time())}.wav"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Always send an absolute, user-expanded path to SuperCollider so that
        # the recording ends up exactly where we expect it, regardless of the
        # SC server's working directory.
        output_path = output_path.expanduser().resolve()

        # 1) Start SC recording (pass duration)
        self._sc_record_start(output_path, duration)
        time.sleep(0.25)

        # 2) Evaluate Tidal code
        code = f'd{self.stream} $ ({rhs_pattern_expr}) # orbit {self.orbit}'
        self.tidal.eval(code)

        # 3) Wait window
        time.sleep(max(0.0, duration))

        # 4) Silence our stream and stop
        self.tidal.silence_stream(self.stream)
        time.sleep(0.1)
        self._sc_record_stop()

        # 5) Wait up to ~3s for SC to finish writing the WAV
        for _ in range(60):
            if output_path.exists() and output_path.stat().st_size > 2000:  # >2KB: not a header-only file
                break
            time.sleep(0.05)

        print(f"[Backend] Audio recorded to {output_path}")
        if playback_after:
            self.play_file(output_path)

        return output_path

    def play_file(self, path: Path):
        """Best-effort local playback."""
        path = Path(path)
        if not path.exists():
            print(f"[Backend] Not found: {path}")
            return
        try:
            system = platform.system()
            if system == "Darwin":
                subprocess.run(["afplay", str(path)], check=False)
            elif system == "Windows":
                import winsound
                winsound.PlaySound(str(path), winsound.SND_FILENAME)
            else:
                for cmd in (["aplay", str(path)], ["paplay", str(path)],
                            ["ffplay", "-nodisp", "-autoexit", str(path)]):
                    try:
                        subprocess.run(cmd, check=False)
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            print(f"[Backend] Playback error: {e}")

    def close(self):
        """Clean up resources."""
        self.tidal.close()