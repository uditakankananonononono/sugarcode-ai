"""Current helper read-error behavior, not OS absence or reaping proof."""
import errno

import pytest

from process_terminal_poll_h27 import poll_terminal_status


@pytest.mark.parametrize('error,expected', [
    (ProcessLookupError(errno.ESRCH, 'synthetic vanished process'), 'ProcessLookupError'),
    (OSError(errno.EIO, 'synthetic read failure'), 'OSError'),
])
def test_non_file_missing_os_errors_return_failure_without_retry(error, expected):
    calls = []
    sleeps = []
    def read():
        calls.append(1)
        raise error
    result = poll_terminal_status(read, monotonic=lambda: 0.0, sleep=sleeps.append,
                                  expected_pid=123, expected_name='python')
    assert result == {
        'terminal': False, 'last_state': None, 'error': expected,
        'elapsed': 0.0, 'samples': ((0.0, None, expected),),
        'identity_diagnostic': {
            'expected_pid': 123, 'observed_pid': None,
            'expected_name': 'python', 'observed_name': None,
            'name_matches_when_available': None,
        },
    }
    assert calls == [1]
    assert sleeps == []
