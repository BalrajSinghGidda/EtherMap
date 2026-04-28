#!/usr/bin/env python3
"""Start EtherMap web servers for local demo use."""

import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
EVENTS_SERVER = os.path.join(ROOT, "events-server.py")
SIGNALING_SERVER = os.path.join(ROOT, "auth_signaling.py")


def spawn(name, script_path):
    proc = subprocess.Popen([sys.executable, script_path], cwd=ROOT)
    print(f"[start] {name} pid={proc.pid}")
    return proc


def terminate_all(procs):
    for p in procs:
        if p.poll() is None:
            p.terminate()
    deadline = time.time() + 4
    for p in procs:
        if p.poll() is not None:
            continue
        remaining = max(0, deadline - time.time())
        try:
            p.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            p.kill()


def main():
    print("Starting EtherMap demo stack")
    print("  events server:   http://127.0.0.1:5000")
    print("  signaling server: http://127.0.0.1:5050")
    print("Press Ctrl+C to stop.")

    procs = [
        spawn("events-server", EVENTS_SERVER),
        spawn("auth_signaling", SIGNALING_SERVER),
    ]

    def handle_stop(_sig, _frame):
        terminate_all(procs)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    try:
        while True:
            for p in procs:
                code = p.poll()
                if code is not None:
                    print(f"[stop] child pid={p.pid} exited with {code}")
                    terminate_all(procs)
                    return code if code else 0
            time.sleep(0.5)
    finally:
        terminate_all(procs)


if __name__ == "__main__":
    raise SystemExit(main())
