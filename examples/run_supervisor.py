"""Supervisor script to run simulation robustly with timeouts and restarts.

This script launches the main simulation and monitors its output.
If a generation takes longer than TIMEOUT_SECONDS, the process is killed
and restarted. The simulation script will automatically resume from the
last checkpoint.
"""

import subprocess
import time
import threading
import sys
import os
import signal

# Configuration
TIMEOUT_SECONDS = 180  # 5 minutes per generation
SCRIPT_PATH = "examples/run_simulation.py"

def reader_thread(proc, activity_callback):
    """Reads stdout from process and updates activity timestamp on progress."""
    try:
        # iter(proc.stdout.readline, b'') works for binary streams
        for line in iter(proc.stdout.readline, b''):
            line_str = line.decode('utf-8', errors='replace')
            sys.stdout.write(line_str)
            # No manual flush needed usually if we write to stdout, but good practice
            
            # Reset timer on significant progress markers
            # "Starting generation" indicates we entered the loop
            # "Finished generation" indicates we completed a loop
            # "Evaluated" indicates progress within generation
            if any(k in line_str for k in [
                "Finished generation", 
                "Starting generation", 
                "Evaluated",
                "Offspring complete"
            ]):
                activity_callback()
                
    except (ValueError, OSError):
        pass
    finally:
        if proc.stdout:
            try:
                proc.stdout.close()
            except:
                pass

def run_once():
    print(f"\n[Supervisor] Starting simulation process: {SCRIPT_PATH}")
    
    # Ensure unbuffered output so we see lines immediately
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    proc = subprocess.Popen(
        [sys.executable, SCRIPT_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        env=env
    )
    
    # Track last activity time in a mutable container
    last_activity = [time.time()]
    
    def update_activity():
        last_activity[0] = time.time()
        
    # Start monitoring thread
    t = threading.Thread(target=reader_thread, args=(proc, update_activity))
    t.daemon = True
    t.start()
    
    # Monitor loop
    try:
        while proc.poll() is None:
            time.sleep(1)
            elapsed = time.time() - last_activity[0]
            
            if elapsed > TIMEOUT_SECONDS:
                print(f"\n[Supervisor] 🚨 TIMEOUT DETECTED! (No progress markers for {elapsed:.1f}s)")
                print("[Supervisor] Killing hung process...")
                try:
                    # Try terminate first
                    proc.terminate()
                    time.sleep(2)
                    if proc.poll() is None:
                        # Force kill if still alive
                        print("[Supervisor] Force killing...")
                        os.kill(proc.pid, signal.SIGKILL)
                except Exception as e:
                    print(f"[Supervisor] Error killing process: {e}")
                    
                return "TIMEOUT"
                
    except KeyboardInterrupt:
        print("\n[Supervisor] Keyboard interrupt, stopping child...")
        proc.terminate()
        return "INTERRUPTED"
            
    return "FINISHED"

def main():
    print(f"[Supervisor] Monitoring for hangs (> {TIMEOUT_SECONDS}s silence)")
    
    while True:
        result = run_once()
        
        if result == "FINISHED":
            print("[Supervisor] Simulation process exited normally. All done.")
            break
        elif result == "INTERRUPTED":
            break
        elif result == "TIMEOUT":
            print("[Supervisor] Restarting simulation in 5 seconds...")
            time.sleep(5)
        else:
            # Should not happen
            print(f"[Supervisor] Unexpected result: {result}")
            time.sleep(5)

if __name__ == "__main__":
    main()
