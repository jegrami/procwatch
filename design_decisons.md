# ProcWatch

A minimal process supervisor. Launches a child process, restarts it on
failure with exponential backoff, and logs every lifecycle event as
structured JSON. Built to help me understand process management and supervison by modeling how tools like `systemd`, `pm2`,
`supervisord`, and Kubernetes' pod restart policy actually work under the hood.

## What problem this solves

Long-running processes crash. A database connection drops, an unhandled
exception fires, a dependency isn't ready yet. In production, something
has to notice the crash and decide what to do about it. That's the job
of a process supervisor. ProcWatch is a small, from-scratch implementation
of that job, built to understand the mechanism.

## What it does

- Launches a target command as a child process
- Detects how it exited (clean exit vs. crash) via its exit code
- Restarts on failure, with exponential backoff (1s → 2s → 4s → ... capped
  at 30s), resetting the backoff once the process is healthy again
- Handles Ctrl+C (SIGINT) gracefully: sends SIGTERM to the child, waits up
  to 5s, escalates to SIGKILL only if the child ignores the polite request
- Writes every lifecycle event (launch, exit, crash, restart, shutdown) as
  one structured JSON line to `procwatch.log`

## What it does *not* do

Following the Unix philosophy of one tool, one job, done well:

- No multi-process orchestration (run one ProcWatch per process you want
  supervised, not one ProcWatch managing many)
- No log rotation, no web dashboard, no config file format
- No dependency management for the child process itself — it assumes the
  child is a runnable command, nothing more


## Design decisions and why

**Exit code, not output parsing, decides success/failure.**
The child's exit code is the canonical, POSIX-standard signal of how a
process finished (`0` = success, non-zero = failure). Parsing stdout for
words like "error" is fragile and format-dependent; the exit code is not.

**Backoff resets on success, not just at startup.**
Backoff should reflect the *current* health of the process, not its
lifetime history. A process that's been stable for days and fails once
should retry quickly — not inherit a 30-second delay from an unrelated
crash loop hours earlier. This mirrors how Kubernetes resets its
`CrashLoopBackOff` counter once a pod stays up long enough.

**SIGTERM before SIGKILL, with a grace period.**
`SIGKILL` is guaranteed to stop a process but gives it no chance to clean
up open files, flush buffers, or release locks. `SIGTERM` is a request a
well-behaved process can catch and exit cleanly from. ProcWatch asks
nicely first and only forces termination if the child ignores the
request within 5 seconds — the same two-step pattern `systemctl stop`
and Kubernetes pod termination use.

**Structured (JSON) logs, not free-text prints.**
A human can read `child crashed, exit code 1`, but a machine can't
reliably query it. Each event is written as a JSON object with a
timestamp, so it can be filtered, aggregated, or fed into real log
tooling (the same principle behind the ELK stack, Datadog, or any log
aggregator ingesting structured logs).

**The log file is opened and closed on every write, not held open.**
Slightly less efficient, but safer: if ProcWatch itself is killed
unexpectedly, no buffered-but-unflushed log line is lost. Given the
entire point of this tool is observing failure, losing the record of a
failure defeats the purpose.

## Usage

```bash
uv sync
uv run procwatch.py <command> [args...]

# example: supervise a script that exits with failure
uv run procwatch.py python flaky_worker.py fail

# example: supervise a script that exits cleanly
uv run procwatch.py python flaky_worker.py success
```

Logs are appended to `procwatch.log` in the project directory, one JSON
object per line.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

## What I'd add next (out of scope for this version, deliberately)

- Configurable restart policy (`always` / `on-failure` / `never`, like
  systemd's `Restart=`)
- Max retry limit before giving up entirely, distinct from backoff
- A `--max-delay` / `--base-delay` CLI flag instead of hardcoded values