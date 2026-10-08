# Queue status without script/output disclosure

python -m sugarcode.cli queue-status --db /path/existing.sqlite --state pending --limit 10

Lists at most 1000 jobs, default 100, FIFO order. Available state filters are
pending, running, uncertain, succeeded, failed, timed_out, cancelled. Projection:
id, sha256, state, timeout, heartbeat, exit_code. No code, stdout or stderr.
This is metadata minimization, NOT anonymization or an access-control boundary.
Job IDs can themselves contain private values. CLI opens SQLite in mode=ro;
missing databases are refused, never created or migrated. No actions/retries.
