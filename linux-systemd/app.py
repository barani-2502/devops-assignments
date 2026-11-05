import os
import signal
import sys
import time
from datetime import datetime


def log(level, message):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} [{level}] {message}", flush=True)


try:
    WORKER_NAME = os.environ.get("WORKER_NAME", "testpress-worker")
    INTERVAL = float(os.environ.get("HEARTBEAT_INTERVAL", "5"))
    CRASH_AFTER_BEATS = int(os.environ.get("CRASH_AFTER_BEATS", "0"))
    CRASH_EXIT_CODE = int(os.environ.get("CRASH_EXIT_CODE", "1"))
    LEAK_MB_PER_BEAT = int(os.environ.get("LEAK_MB_PER_BEAT", "0"))
except ValueError as error:
    log("ERROR", f"Invalid configuration: {error}")
    sys.exit(2)

stop_requested = False


def handle_stop(signum, frame):
    global stop_requested
    log("INFO", f"Received {signal.Signals(signum).name}, shutting down gracefully")
    stop_requested = True


signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)

log("INFO", f"{WORKER_NAME} started, PID={os.getpid()}, interval={INTERVAL}s")

leaked = []
beat = 0
while not stop_requested:
    beat += 1
    log("INFO", f"Heartbeat {beat} PID={os.getpid()}")

    if LEAK_MB_PER_BEAT > 0:
        leaked.append(b"x" * (LEAK_MB_PER_BEAT * 1024 * 1024))
        log("WARN", f"Holding {len(leaked) * LEAK_MB_PER_BEAT} MB of memory")

    if CRASH_AFTER_BEATS > 0 and beat >= CRASH_AFTER_BEATS:
        log("ERROR", f"Simulated crash after {beat} heartbeats, exit code {CRASH_EXIT_CODE}")
        sys.exit(CRASH_EXIT_CODE)

    time.sleep(INTERVAL)

log("INFO", f"{WORKER_NAME} stopped cleanly after {beat} heartbeats")
sys.exit(0)
