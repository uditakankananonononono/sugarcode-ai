"""Explicit test-only containment capability check, not a production fallback."""
import subprocess
import sys
import pytest
from sugarcode.self_improve.isolation import IsolatedRunner, IsolationUnavailable


def containment_unavailable_reason(work):
    runner = IsolatedRunner()
    try:
        command = runner._command(work)
    except IsolationUnavailable as exc:
        return str(exc)
    try:
        probe = subprocess.run(command+[sys.executable, '-I', '-c', 'pass'],
                               capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f'containment preflight failed: {type(exc).__name__}'
    if probe.returncode:
        return 'containment preflight refused: '+probe.stderr.decode(errors='replace')[-1000:]
    return None


@pytest.fixture
def real_containment(tmp_path):
    reason = containment_unavailable_reason(tmp_path)
    if reason is not None:
        pytest.skip('REAL CONTAINMENT NOT VERIFIED in this environment: '+reason)
