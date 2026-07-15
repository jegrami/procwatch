# Procwatch design decisions/rationale

1. Exit code, not output parsing, decides success/failure.

The exit code is the canonical, POSIX-standard signal of how a process
finished (0 = success, non-zero = failure). Parsing stdout for words
like "error" is fragile and format-dependent; the exit code is not.

2. Backoff resets on success, not just at startup.

Backoff should reflect the process's current health, not its lifetime
history. A process that's been stable for days and fails once should
retry quickly, not inherit a 30-second delay from an unrelated crash
loop hours earlier. 

3. SIGTERM before SIGKILL, with a grace period.

SIGKILL is guaranteed to stop a process but gives it no chance to clean
up open files, flush buffers, or release locks. SIGTERM is a request a
well-behaved process can catch and exit cleanly from. ProcWatch asks
nicely first and only forces termination if the child ignores the
request within 5 seconds — the same two-step `systemctl stop` uses.

3. Structured (JSON) logs

Each event is a JSON object with a timestamp, so it
can be filtered, aggregated, or fed into real log tooling.

4. The log file is opened and closed on every write.

Slightly less efficient, but safer: if ProcWatch itself is killed
unexpectedly, no buffered-but-unflushed log line is lost. Given that the
entire point of this tool is observing failure, losing the record of a
failure defeats the purpose.

4. Launch failures are treated differently from crashes.

A missing command (e.g. a typo) can never succeed on retry. It's unlike a
crash, which might be transient. ProcWatch detects this at launch and
stops immediately with a clear error, instead of backoff-looping
forever on something that will never resolve itself.