from types import SimpleNamespace
import subprocess
import sys
import pytest
from seed_core_refusal_contract import is_seed_refusal


def test_actual_scipy_refuses_malformed_seed_without_a_result():
    result = subprocess.run([sys.executable, '-c',
        'from scipy._lib._util import check_random_state; check_random_state([[[[]]]])'],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert not result.stdout
    assert is_seed_refusal(result)


@pytest.mark.parametrize('code,stderr', [
    (0, ''), (1, 'ValueError: unrelated failure'),
    (1, 'ValueError: cannot be used to seed a numpy.random.RandomState instance'),
    (1, 'in check_random_state\nValueError: unrelated failure'),
    (1, 'ImportError: missing module'), (2, 'TypeError: invalid seed'),
    (1, 'TypeError: seed must be an integer'),
])
def test_unrelated_failure_or_valid_result_is_not_accepted(code, stderr):
    assert not is_seed_refusal(SimpleNamespace(returncode=code, stderr=stderr))


@pytest.mark.parametrize('code,stderr', [
    (-11, ''), (1, 'TypeError: unhashable seed'),
    (1, 'RecursionError: maximum recursion depth exceeded'),
    (1, '  File "scipy/_lib/_util.py", line 487, in check_random_state\n'
         "ValueError: '[[[]]]' cannot be used to seed a numpy.random.RandomState instance"),
])
def test_documented_refusals_are_accepted(code, stderr):
    assert is_seed_refusal(SimpleNamespace(returncode=code, stderr=stderr))
