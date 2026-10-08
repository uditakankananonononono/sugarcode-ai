"""Narrow test-only capability refusal classification, never runtime fallback."""
import subprocess
import sys
import pytest
from sugarcode.self_improve.isolation import IsolatedRunner, IsolationUnavailable


_ALLOWED_STDERR = 'bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted'


def containment_unavailable_reason(work):
    runner = IsolatedRunner()
    try:
        command = runner._command(work)
    except IsolationUnavailable as exc:
        if str(exc) == 'bubblewrap executable unavailable':
            return str(exc)
        raise
    # OSError (including missing interpreter/argv), timeout and unexpected runner
    # errors fail the test. A slow probe is not evidence of unavailable capability.
    probe = subprocess.run(command+[sys.executable, '-I', '-c', 'pass'],
                           capture_output=True, timeout=5)
    if probe.returncode:
        stderr = probe.stderr.decode(errors='replace')
        evidence = (f'returncode={probe.returncode}; stdout={probe.stdout[:4096]!r}; '
                    f'stderr={probe.stderr[:4096]!r}')
        if probe.returncode == 1 and stderr.strip() == _ALLOWED_STDERR and not probe.stdout:
            return 'allowlisted loopback capability refusal: '+evidence
        raise RuntimeError('unexplained containment startup failure: '+evidence)
    return None


@pytest.fixture
def real_containment(tmp_path):
    reason = containment_unavailable_reason(tmp_path)
    if reason is not None:
        pytest.skip('REAL CONTAINMENT NOT VERIFIED in this environment: '+reason)
