"""Paired-close failure injections with real children, not OS reliability claims."""
import sys

import pytest

from sugarcode.self_improve import bounded_process as bp


class CloseFault(OSError):
    pass


class CaptureFault(OSError):
    pass


class StreamProxy:
    def __init__(self, stream, error):
        self.stream = stream
        self.error = error
        self.calls = 0

    def fileno(self):
        return self.stream.fileno()

    def close(self):
        self.calls += 1
        self.stream.close()  # Actual close before failure injection.
        if self.error is not None:
            raise self.error


@pytest.mark.parametrize("stdout_fails,stderr_fails,capture_fails", [
    (False, False, False), (True, False, False),
    (False, True, False), (True, True, False), (True, False, True),
])
def test_paired_close_attempts_once_and_preserves_primary_error(
    monkeypatch, stdout_fails, stderr_fails, capture_fails
):
    if bp.os.name != "posix":
        pytest.skip("POSIX capture unavailable; paired cleanup not verified")
    real_spawn = bp.subprocess.Popen
    children = []
    stdout_error = CloseFault("stdout close injection") if stdout_fails else None
    stderr_error = CloseFault("stderr close injection") if stderr_fails else None
    capture_error = CaptureFault("selector registration injection") if capture_fails else None
    def spawn(*args, **kwargs):
        child = real_spawn(*args, **kwargs)
        children.append(child)
        child.stdout = StreamProxy(child.stdout, stdout_error)
        child.stderr = StreamProxy(child.stderr, stderr_error)
        return child
    def fail_register(*args, **kwargs):
        raise capture_error
    caught = None
    result = None
    try:
        with monkeypatch.context() as patch:
            patch.setattr(bp.subprocess, "Popen", spawn)
            if capture_fails:
                patch.setattr(bp.selectors.BaseSelector, "register", fail_register)
                patch.setattr(bp.selectors._BaseSelectorImpl, "register", fail_register)
            try:
                result = bp.run_bounded_process(
                    [sys.executable, "-c", "print('synthetic')"], timeout_seconds=2
                )
            except BaseException as exc:
                caught = exc
        assert len(children) == 1
        child = children[0]
        assert child.returncode is not None, "direct child not reaped"
        assert child.stdout.calls == child.stderr.calls == 1, "paired close omitted/retried"
        assert child.stdout.stream.closed and child.stderr.stream.closed
        primary = stdout_error or stderr_error or capture_error
        assert caught is primary, "close-error precedence/identity changed"
        if capture_fails:
            assert caught.__context__ is capture_error
        if primary is None:
            assert result.exit_code == 0 and result.stdout == b"synthetic\n"
            assert not result.timed_out and result.overflow_stream is None
    finally:
        # Use underlying streams, never the faulting proxy. No child or fd may
        # leak even when a source mutation causes an assertion failure.
        for child in children:
            if child.poll() is None:
                bp._kill_group(child)
                child.wait(timeout=3)
            child.stdout.stream.close()
            child.stderr.stream.close()
