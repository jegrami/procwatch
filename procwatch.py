import sys
import subprocess 
import time
import json
import argparse
from datetime import datetime, timezone


def parse_args():
    parser = argparse.ArgumentParser(
        prog="procwatch", 
        description="Supervise a process. Restart on failure with exponential backoff"
    )
    parser.add_argument(
        "--base-delay", type=float, default=2.0,
        help="iniitial restart delay in seconds (default: 2.0)"
    )

    parser.add_argument(
        "--max-delay", type=float, default=30.0,
        help="maximum restart delay in seconds (default: 30.0)"
    )

    parser.add_argument(
        "command", nargs=argparse.REMAINDER,
        help=(
        "The program to run and keep alive, preceded by '--' to separate "
        "it from procwatch's own flags. "
        "Example: procwatch --base-delay 2 -- python server.py"
    )
    ) 
    return parser.parse_args()

LOG_FILE = "procwatch.log"

def log_event(event, **details): 

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **details,
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    print(f"[procwatch] {event}: {details}")

def run_once(command):
    log_event("launching", command=command)

    try: 
        process = subprocess.Popen(command)
    except FileNotFoundError:
        log_event("launch failed", command=command, 
                  reason="command not found")
        print(f"[procwatch] ERROR: command not found {command[0]}")
        raise


    try: 
        exit_code = process.wait()
    except KeyboardInterrupt:
        log_event("interrupt received")
        process.terminate() # ask nicely first (SIGTERM)

        try: 
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log_event("force_kill", reason="child process too stubborn to obey SIGTERM, killing by force") # SIGKILL
            process.kill()
        raise

    log_event("child_exited", exit_code=exit_code)
    return exit_code

def supervise(command, base_delay=1, max_delay=30): 

    failures = 0

    while True:

        try:
            exit_code = run_once(command)
        except FileNotFoundError:
            log_event("supervision ended", reason="command not found")
            return
        except KeyboardInterrupt:
            log_event("shutdoown complete")
            return 
        
        if exit_code == 0:
            log_event("supervision ended", reason="clean_exit")
            break
        
        delay = min(base_delay * (2 ** failures), max_delay)
        log_event("child process crashed", exit_code=exit_code, restart_delay=delay)
        
        try: 
            time.sleep(delay)
        except KeyboardInterrupt: 
            log_event("shutdown requested", phase="backoff wait")
            log_event("shutdown complete")
            return 
        

        failures += 1


if __name__ == "__main__":
    args = parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        print("[procwatch] ERROR: no command given to supervise")
        print("Usage: uv run procwatch.py [--base-delay N] [--max-delay N] -- <command> [args...]")
        sys.exit(1)

    supervise(command, base_delay=args.base_delay, max_delay=args.max_delay)