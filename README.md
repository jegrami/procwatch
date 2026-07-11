# ProcWatch

A minimal process supervisor built to model how tools like `systemd`, `pm2`,
`supervisord`, and Kubernetes' pod restart policy work.


## What it does

- Launches a target command as a child process
- Detects how it exited (clean exit vs. crash) via its exit code
- Restarts on failure, with exponential backoff (1s, 2s, 4s, ... capped
  at 30s), resetting the backoff once the process is healthy again
- Handles Ctrl+C (SIGINT) gracefully: sends SIGTERM to the child, waits up
  to 5s, escalates to SIGKILL only if the child ignores the polite request
- Writes every lifecycle event (launch, exit, crash, restart, shutdown) as
  one structured JSON line to `procwatch.log`
- Backoff delays are configurable via `--base-delay` and `--max-delay`
  flags, defaults to 2s / 30s if omitted

## What this tiny tool does *not* do

Following the Unix philosophy of "one tool, one job, done well":

- No multi-process orchestration (run one ProcWatch per process you want
  supervised, not one ProcWatch managing many)
- No log rotation, no web dashboard, no config file format
- No dependency management for the child process itself; it assumes the
  child is a runnable command, nothing more


## Usage

```bash
uv sync
uv run procwatch.py [--base-delay N] [--max-delay N] --  [args...]

# examples
uv run procwatch.py -- python flaky_worker.py
uv run procwatch.py --base-delay 1 --max-delay 10 -- python flaky_worker.py
```

The `--` separates procwatch's own flags from the command being supervised.
Logs are appended to `procwatch.log`, one JSON object per line.


## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

## TODOs
- [ ] Add configurable restart policy (`always` / `on-failure` / `never`, like
      systemd's `Restart=`)
- [ ] Add max retry limit before giving up entirely

- [x] A `--max-delay` / `--base-delay` CLI flag instead of hardcoded values

