"""Current helper read-error behavior, not OS absence or reaping proof."""
import errno

import pytest

from process_terminal_poll_h27 import poll_terminal_status


@pytest.mark.parametrize('error,expected', [
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


def test_esrch_means_process_already_terminated():
    def read():
        raise ProcessLookupError(errno.ESRCH, 'synthetic vanished process')
    result = poll_terminal_status(read, monotonic=lambda: 0.0,
                                  sleep=lambda seconds: pytest.fail('unexpected retry'))
    assert result['terminal'] is True
    assert result['last_state'] is None
    assert result['error'] is None
    assert result['samples'] == ((0.0, None, None),)


def test_still_alive_process_is_not_terminal():
    result = poll_terminal_status(lambda: 'Name: python\nPid: 123\nState: S (sleeping)\n',
                                  monotonic=lambda: 0.0, sleep=lambda seconds: None,
                                  timeout=0.0, expected_pid=123, expected_name='python')
    assert result['terminal'] is False
    assert result['last_state'] == 'S'
    assert result['error'] is None


def test_non_esrch_process_lookup_error_is_not_terminal():
    def read():
        raise ProcessLookupError(errno.EIO, 'not an absence indication')
    result = poll_terminal_status(read, monotonic=lambda: 0.0, sleep=lambda seconds: None)
    assert result['terminal'] is False
    assert result['error'] == 'ProcessLookupError'
