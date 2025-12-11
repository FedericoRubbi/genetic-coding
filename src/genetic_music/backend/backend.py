"""
Backend for driving TidalCycles via GHCi and recording audio via SuperCollider.
- Requires: Tidal installed, a valid BootTidal.hs path, SuperDirt running.
"""

import os
import time
import shlex
import platform
import subprocess
import select
import sys
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
        
        # Buffer tracking for debugging
        self._total_bytes_read = 0
        self._eval_count = 0

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
        # Optional: set a distinct prompt so we can detect readiness.
        # IMPORTANT: we deliberately avoid blocking forever waiting for the
        # prompt token here. In some environments BootTidal or user config can
        # interfere with the prompt logic, and a blocking read can deadlock
        # the whole backend. Instead, we:
        #   - request a prompt
        #   - drain whatever output is available for a bounded time window
        # This is enough to ensure GHCi is responsive without risking hangs.
        self._write(':set prompt "tidal> "')

        debug_startup = os.environ.get("GHCI_DEBUG_BUFFER", "false").lower() == "true"
        # Best-effort, non-blocking drain of startup output (up to ~5s).
        # If nothing arrives or the prompt doesn't appear, we still proceed,
        # and later eval() calls will surface problems via exceptions.
        self._read_available(timeout=5.0, debug=debug_startup)

    def _quote(self, p: Path) -> str:
        return shlex.quote(str(p))

    def _write(self, line: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read_available(self, timeout: float = 0.2, debug: bool = False) -> str:
        """Best-effort, non-blocking read to drain output.
        
        This is CRITICAL to prevent pipe deadlock. GHCi writes output
        to stdout, and if we don't read it, the pipe buffer fills up
        (typically 65KB) and GHCi blocks on write operations.
        """
        if self.proc.stdout is None:
            return ""
            
        out = []
        end = time.time() + timeout
        bytes_read = 0
        
        # Use select on Unix-like systems for efficient non-blocking I/O
        if hasattr(select, 'select'):
            while time.time() < end:
                if self.proc.poll() is not None:
                    break
                    
                # Check if data is available with a short timeout
                ready, _, _ = select.select([self.proc.stdout], [], [], 0.01)
                if ready:
                    try:
                        chunk = self.proc.stdout.read(1)
                        if chunk:
                            out.append(chunk)
                            bytes_read += 1
                        else:
                            break
                    except (IOError, OSError) as e:
                        if debug:
                            print(f"[GHCi-Buffer] Error reading: {e}")
                        break
                else:
                    # No data available, check if we should keep waiting
                    if out:  # If we got some data, we can stop
                        break
        else:
            # Fallback for Windows: just try to read with timeout
            # This is less efficient but works
            while time.time() < end:
                if self.proc.poll() is not None:
                    break
                try:
                    chunk = self.proc.stdout.read(1)
                    if chunk:
                        out.append(chunk)
                        bytes_read += 1
                    else:
                        break
                except (IOError, OSError) as e:
                    if debug:
                        print(f"[GHCi-Buffer] Error reading: {e}")
                    break
        
        result = "".join(out)
        self._total_bytes_read += bytes_read
        
        if debug and bytes_read > 0:
            preview = result[:100].replace('\n', '\\n')
            print(f"[GHCi-Buffer] Read {bytes_read} bytes (total: {self._total_bytes_read}): {preview}...")
                    
        return result

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

    def eval(self, code: str, debug: bool = False):
        """
        Evaluate a single Tidal line. Example:
          tidal.eval('d12 $ s "bd sd" # orbit 8')
        """
        self._eval_count += 1
        
        if debug:
            code_preview = code[:60].replace('\n', ' ')
            print(f"[GHCi-Eval #{self._eval_count}] Sending: {code_preview}...")
        
        self._write(code)
        
        # CRITICAL: Drain output buffer to prevent pipe deadlock
        # Without this, after ~10 evaluations the stdout buffer fills up
        # and GHCi blocks, causing the entire process to hang
        self._read_available(timeout=0.1, debug=debug)
        
        if debug:
            print(f"[GHCi-Eval #{self._eval_count}] After drain: {self._total_bytes_read} total bytes read")

    def silence_stream(self, stream: int, debug: bool = False):
        self.eval(f"d{stream} silence", debug=debug)

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
        debug_buffer: bool = None,  # Enable buffer debugging
    ):
        self.tidal = TidalGhci(boot_tidal_path=boot_tidal_path, ghci_cmd=ghci_cmd)
        self.osc = udp_client.SimpleUDPClient(sc_host, sc_port)
        self.orbit = int(orbit)
        self.stream = int(stream)
        self.out_dir = Path("data/outputs")
        
        # Check environment variable or use parameter
        if debug_buffer is None:
            debug_buffer = os.environ.get('GHCI_DEBUG_BUFFER', 'false').lower() == 'true'
        self.debug_buffer = debug_buffer
        
        if self.debug_buffer:
            print(f"[Backend] Buffer debugging ENABLED")

    # ---- SuperCollider recording helpers ----
    def _sc_record_start(self, path: Path, duration: float):
        self.osc.send_message("/gp/startRecord", [str(path), float(duration)])

    def _sc_record_stop(self):
        self.osc.send_message("/gp/stopRecord", [])

    # ---- Public API ----
    def play_tidal_code(
        self,
        rhs_pattern_expr: str,
        duration: float = 4.0,
        output_path: Optional[Path] = None,
        playback_after: bool = False,
    ) -> Path:
        """
        Record a Tidal pattern constructed as a RIGHT-HAND-SIDE expression.
        Example rhs:  s "bd sd [bd sn]" # speed 1.1

        We send:      d{stream} $ (rhs) # orbit {orbit}

        Returns: Path to the recorded WAV.
        """
        # Check if GHCi process is still alive
        if self.tidal.proc.poll() is not None:
            raise RuntimeError(f"GHCi process has died (exit code: {self.tidal.proc.poll()})")
        
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
        try:
            self._sc_record_start(output_path, duration)
        except Exception as e:
            raise RuntimeError(f"Failed to start SC recording: {e}")
        
        time.sleep(0.25)

        # 2) Evaluate Tidal code
        code = f'd{self.stream} $ ({rhs_pattern_expr}) # orbit {self.orbit}'
        try:
            self.tidal.eval(code, debug=self.debug_buffer)
        except Exception as e:
            raise RuntimeError(f"Failed to evaluate Tidal code: {e}")

        # 3) Wait window
        time.sleep(max(0.0, duration))

        # 4) Silence our stream and stop
        try:
            self.tidal.silence_stream(self.stream, debug=self.debug_buffer)
            time.sleep(0.1)
            self._sc_record_stop()
        except Exception as e:
            print(f"[Backend] Warning: Error during cleanup: {e}")

        # 5) Wait up to ~5s for SC to finish writing the WAV
        max_wait_time = 5.0
        wait_start = time.time()
        file_ready = False
        
        for _ in range(100):  # Check up to 100 times (5 seconds at 0.05s each)
            if output_path.exists() and output_path.stat().st_size > 2000:  # >2KB: not a header-only file
                file_ready = True
                break
            if time.time() - wait_start > max_wait_time:
                break
            time.sleep(0.05)

        if not file_ready:
            print(f"[Backend] WARNING: Audio file not ready after {max_wait_time}s: {output_path}")
            # Still return the path, but caller should check file existence
        else:
            wait_duration = time.time() - wait_start
            print(f"[Backend] Audio recorded to {output_path} (wait: {wait_duration:.2f}s)")
        
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