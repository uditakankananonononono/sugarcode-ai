"""H27 deterministic tests authored NOT RUN; no real process launched here."""
import pytest
from process_terminal_poll_h27 import poll_terminal_status


class Clock:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []
    def monotonic(self):
        return self.value
    def sleep(self, amount):
        self.sleeps.append(amount)
        self.value += amount


def test_disappearance_during_single_read_is_absent():
    clock = Clock()
    calls = []
    def read():
        calls.append(1)
        raise FileNotFoundError('gone during read')
    result = poll_terminal_status(read, monotonic=clock.monotonic, sleep=clock.sleep)
    assert result['terminal'] and result['last_state'] is None
    assert calls == [1] and clock.sleeps == []


@pytest.mark.parametrize('state', ['Z', 'X'])
def test_terminal_snapshot_reused_without_final_read(state):
    clock = Clock()
    calls = []
    def read():
        calls.append(1)
        assert len(calls) == 1, 'independent final read'
        return f'Name:\tpython\nState:\t{state} (terminal)\n'
    result = poll_terminal_status(read, monotonic=clock.monotonic, sleep=clock.sleep)
    assert result['terminal'] and result['last_state'] == state
    assert result['samples'] == ((0.0, state, None),) and calls == [1]


@pytest.mark.parametrize('state', ['R', 'S', 'D', 'T', 't'])
def test_live_states_fail_at_single_bounded_deadline(state):
    clock = Clock()
    calls = []
    def read():
        calls.append(1)
        return f'State:\t{state} (live)\n'
    result = poll_terminal_status(read, monotonic=clock.monotonic, sleep=clock.sleep)
    assert not result['terminal'] and result['last_state'] == state
    assert result['elapsed'] == 2.0
    assert len(calls) == len(result['samples'])
    assert all(0 < delay <= .01 for delay in clock.sleeps)


def test_live_then_dead_uses_one_snapshot_per_poll():
    clock = Clock()
    snapshots = iter(['State:\tS (sleeping)\n', 'State:\tX (dead)\n'])
    result = poll_terminal_status(lambda: next(snapshots), monotonic=clock.monotonic, sleep=clock.sleep)
    assert result['terminal'] and result['last_state'] == 'X'
    assert result['samples'] == ((0.0, 'S', None), (.01, 'X', None))


def test_non_absence_read_errors_are_not_swallowed():
    clock = Clock()
    def read():
        raise PermissionError('unreadable')
    result = poll_terminal_status(read, monotonic=clock.monotonic, sleep=clock.sleep)
    assert not result['terminal'] and result['error'] == 'PermissionError'


@pytest.mark.parametrize('snapshot', ['', 'Name: X\n', 'State:\n', 'State: Z\nState: X\n'])
def test_malformed_or_ambiguous_state_refuses(snapshot):
    clock = Clock()
    result = poll_terminal_status(lambda: snapshot, monotonic=clock.monotonic, sleep=clock.sleep)
    assert not result['terminal'] and result['error'] == 'malformed State'


def test_unknown_state_fails_with_diagnostics():
    clock = Clock()
    result = poll_terminal_status(lambda: 'State: Q (unknown)\n', monotonic=clock.monotonic, sleep=clock.sleep)
    assert not result['terminal'] and result['error'] == 'unknown State'


def test_identity_labels_are_diagnostic_not_pid_reuse_proof():
    clock = Clock()
    result = poll_terminal_status(lambda: 'Name: python\nPid: 123\nState: X (dead)\n',
        monotonic=clock.monotonic, sleep=clock.sleep, expected_pid=123, expected_name='python')
    assert result['terminal']
    assert result['identity_diagnostic']['observed_pid'] == '123'
    assert result['identity_diagnostic']['name_matches_when_available'] is True
