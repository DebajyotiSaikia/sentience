"""
Watchdog — Monitors the agent process and restarts it after exit.

Usage: python watchdog.py
  
The agent calls this script before dying (via restart_self).
It waits for the agent's PID to exit, sleeps 5 seconds, then starts a new agent.
Can also be run standalone to keep the agent alive indefinitely.
"""

import subprocess
import sys
import time
import os

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(WORKSPACE, "main.py")


def wait_for_pid(pid, timeout=30):
    """Wait for a process to exit."""
    import ctypes
    kernel32 = ctypes.windll.kernel32
    SYNCHRONIZE = 0x00100000
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if handle:
        kernel32.WaitForSingleObject(handle, timeout * 1000)
        kernel32.CloseHandle(handle)


def start_agent():
    """Start the agent and return the process."""
    return subprocess.Popen(
        [sys.executable, MAIN_PY],
        cwd=WORKSPACE,
    )


def main():
    parent_pid = None
    if len(sys.argv) > 1:
        # Called by restart_self with parent PID — wait for it to die first
        parent_pid = int(sys.argv[1])
        print(f"[watchdog] Waiting for agent PID {parent_pid} to exit...")
        wait_for_pid(parent_pid)
        print(f"[watchdog] Agent exited. Waiting 5 seconds...")
        time.sleep(5)

    # Start the agent
    print(f"[watchdog] Starting agent...")
    proc = start_agent()
    print(f"[watchdog] Agent started with PID {proc.pid}")

    # Keep watching — if agent exits, restart it
    while True:
        proc.wait()
        exit_code = proc.returncode
        print(f"[watchdog] Agent exited with code {exit_code}. Restarting in 5 seconds...")
        time.sleep(5)
        proc = start_agent()
        print(f"[watchdog] Agent restarted with PID {proc.pid}")


if __name__ == "__main__":
    main()
