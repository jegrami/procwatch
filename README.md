# ProcWatch

ProcWatch runs a command as a child process and keeps it running. If the
command exits with a non-zero status, ProcWatch restarts it, waiting
longer between each successive failure (1s, 2s, 4s... capped at 30s by
default) instead of restarting it instantly every time, which would just
pile restart attempts on top of whatever already caused it to fail. If
it exits with status 0, ProcWatch takes that as "done" and stops.

This is a small, deliberately narrow reimplementation of what systemd's
`Restart=`, pm2, and supervisord all do. Building  this tool helped me understand
process supervision — exit codes, signal handling, backoff. 

Rationale for the non-obvious choices like backoff, signal handling,
logging format are in [design-decisons.md](DESIGN.md).

Procwatch supervises one process per invocation. If you want to supervise five
processes, run five instances of ProcWatch. There is no manager-of-managers,
no config file, no web dashboard, and none are planned. That's not what
this is for.

## Usage

    uv sync
    uv run procwatch.py [--base-delay N] [--max-delay N] -- <command> [args...]

The double dash (`--`) matters. Everything after it is passed straight through to the
child process. Without it, ProcWatch has no reliable way to
tell its own flags apart from the child's.

    uv run procwatch.py -- python flaky_worker.py fail
    uv run procwatch.py --base-delay 2 --max-delay 10 -- python server.py

Requires Python 3.10 or later and [uv](https://docs.astral.sh/uv/). I
developed against 3.14 but the `pyproject.toml` floor is 3.10, and I tested
against it directly with `uv run --python 3.10` to ensure  it works with that version. 

## Shutdown

Ctrl+C sends SIGTERM to the child and waits five seconds, escalating to
SIGKILL if it hasn't exited by then.

## Logging

Launch, exit, crash, restart, and shutdown events are written to
`procwatch.log` as one JSON object per line, in addition to being printed
to the terminal.

A launch failure (bad command, typo, missing binary) is not retried. ProcWatch logs it and stops immediately instead of backing off forever against something that can't succeed.

## Limitations

1. There's no max-retry ceiling yet. A broken process will back off to 30 seconds and sit there indefinitely rather than eventually giving up. 

2. No configurable restart policy (`always` / `on-failure` / `never`). Procwatch
currently always retries on failure and never retries on success, and that's it. 

3. This has been tested against `flaky_worker.py` (included, a deliberately
controllable dummy process), `python -m http.server`, `ping`, and `node server.js`. It has
not been run against anything with real production stakes, and I wouldn't
put it in front of anything that matters yet.