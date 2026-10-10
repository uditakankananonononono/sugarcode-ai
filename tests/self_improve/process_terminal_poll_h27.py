"""Test-only proc status polling; not a product/reaping helper."""

def poll_terminal_status(read_status, *, monotonic, sleep, timeout=2.0,
                         expected_pid=None, expected_name=None):
    start = monotonic()
    deadline = start + timeout
    samples = []
    while True:
        state = None
        error = None
        observed_name = None
        observed_pid = None
        try:
            snapshot = read_status()  # One read, no exists/final re-read.
        except FileNotFoundError:
            pass
        except OSError as exc:
            error = type(exc).__name__
        else:
            fields = {}
            for line in snapshot.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    fields.setdefault(key, []).append(value.strip())
            states = fields.get('State', [])
            if len(states) != 1 or not states[0].split():
                error = 'malformed State'
            else:
                state = states[0].split()[0]
                if state not in ('R', 'S', 'D', 'T', 't', 'Z', 'X'):
                    error = 'unknown State'
            observed_name = fields.get('Name', [None])[0]
            observed_pid = fields.get('Pid', [None])[0]
        elapsed = monotonic() - start
        samples.append((elapsed, state, error))
        terminal = error is None and (state is None or state in ('Z', 'X'))
        result = {'terminal': terminal, 'last_state': state, 'error': error,
                  'elapsed': elapsed, 'samples': tuple(samples),
                  'identity_diagnostic': {'expected_pid': expected_pid,
                      'observed_pid': observed_pid, 'expected_name': expected_name,
                      'observed_name': observed_name,
                      'name_matches_when_available': None if observed_name is None or expected_name is None
                          else observed_name == expected_name}}
        # Identity is a diagnostic label, not a PID-reuse/authorization predicate.
        if error is not None or terminal or start + elapsed >= deadline:
            return result
        sleep(min(.01, max(0.0, deadline - (start + elapsed))))
