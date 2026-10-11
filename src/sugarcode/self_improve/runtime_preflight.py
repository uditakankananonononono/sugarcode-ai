"""Trusted runner dependency check before any candidate code is written or run."""
from __future__ import annotations

from .bounded_process import run_bounded_process


class SandboxEnvironmentUnavailable(RuntimeError):
    """The runner cannot evaluate candidates; this is not a candidate failure."""


def require_pytest(command_prefix, *, env=None, cwd=None):
    """Check the exact child environment with bounded output and a fixed deadline.

    No candidate import, pytest collection, plugin loading or execution occurs.
    Do not fall back to the parent's user-site packages or relax isolation.
    """
    try:
        probe = run_bounded_process(
            [*command_prefix, '-c', 'import pytest'],
            timeout_seconds=5, env=env, cwd=cwd, output_bytes=4096,
            tail_bytes=1000)
    except OSError as exc:
        raise SandboxEnvironmentUnavailable(
            'sandbox environment unavailable: child interpreter could not start; '
            'install pytest in the trusted child runtime') from exc
    if probe.timed_out or probe.overflow_stream is not None or probe.exit_code != 0:
        raise SandboxEnvironmentUnavailable(
            'sandbox environment unavailable: child interpreter cannot import pytest '
            'within the dependency preflight limits; install pytest in the trusted '
            'child runtime (user-site-only installs are unavailable under '
            'environment scrubbing or isolated mode)')
