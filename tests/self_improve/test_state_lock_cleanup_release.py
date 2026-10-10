"""Synthetic acquisition/cleanup failures. Not an OS close reliability claim."""
import threading

import pytest

from sugarcode.self_improve import state_lock as sl


class AcquisitionFault(OSError):
    pass


class CleanupFault(OSError):
    pass


def other_thread_attempt(lock):
    results = []
    def attempt():
        try:
            with lock:
                results.append(("acquired", lock._depth))
        except BaseException as exc:
            results.append((type(exc).__name__, str(exc)))
    worker = threading.Thread(target=attempt, daemon=True)
    worker.start()
    worker.join(3)
    assert not worker.is_alive(), "bounded follow-up did not exit"
    return results


def release_mutant_leak(lock):
    # Only this test thread acquired the failed entry's RLock. Never release a
    # successful holder's lock. Mutations may have stranded exactly one depth.
    try:
        lock._thread_lock.release()
    except RuntimeError:
        pass


@pytest.mark.parametrize("where,cleanup_fault", [
    ("fstat", False), ("fstat", True), ("flock", True),
])
def test_failed_acquisition_releases_depth_even_when_cleanup_raises(
    tmp_path, monkeypatch, where, cleanup_fault
):
    if sl.fcntl is None or not hasattr(sl.os, "O_NOFOLLOW"):
        pytest.skip("POSIX prerequisite absent; acquisition path not verified")
    lock = sl.shared_state_lock(tmp_path / "synthetic.json", timeout=0.05)
    real_close = sl.os.close
    closes = []
    def fail(*args, **kwargs):
        raise AcquisitionFault("injected acquisition failure")
    def close(fd):
        closes.append(fd)
        real_close(fd)
        if cleanup_fault:
            raise CleanupFault("injected failure after actual close")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(sl.os, "close", close)
            if where == "fstat":
                patch.setattr(sl.os, "fstat", fail)
            else:
                patch.setattr(sl.fcntl, "flock", fail)
            expected = CleanupFault if cleanup_fault else AcquisitionFault
            caught = None
            try:
                with lock:
                    pass
            except BaseException as exc:
                caught = exc
            assert isinstance(caught, expected), "acquisition/cleanup exception contract changed"
            if cleanup_fault:
                assert isinstance(caught.__context__, AcquisitionFault)
        assert len(closes) == 1, "cleanup must not retry close"
        assert lock._fd is None and lock._depth == 0
        assert other_thread_attempt(lock) == [("acquired", 1)], "failed entry leaked RLock"
    finally:
        release_mutant_leak(lock)


def test_capability_refusal_releases_depth_without_close(tmp_path, monkeypatch):
    lock = sl.shared_state_lock(tmp_path / "capability.json", timeout=0.05)
    closes = []
    try:
        with monkeypatch.context() as patch:
            patch.setattr(sl, "fcntl", None)
            patch.setattr(sl.os, "close", lambda fd: closes.append(fd))
            with pytest.raises(sl.StateLockUnavailable):
                with lock:
                    pytest.fail("unlocked platform fallback")
        assert closes == []
        assert lock._fd is None and lock._depth == 0
        if sl.fcntl is None or not hasattr(sl.os, "O_NOFOLLOW"):
            pytest.skip("restored POSIX capability absent; follow-up not verified")
        assert other_thread_attempt(lock) == [("acquired", 1)], "capability refusal leaked RLock"
    finally:
        release_mutant_leak(lock)


def test_success_and_reentrant_depth_remain_owned(tmp_path):
    if sl.fcntl is None or not hasattr(sl.os, "O_NOFOLLOW"):
        pytest.skip("POSIX prerequisite absent; success path not verified")
    lock = sl.shared_state_lock(tmp_path / "success.json", timeout=0.05)
    with lock:
        first_fd = lock._fd
        with lock:
            assert lock._depth == 2 and lock._fd == first_fd
        assert lock._depth == 1 and lock._fd == first_fd
        results = other_thread_attempt(lock)
        assert results[0][0] == "StateLockTimeout", "successful holder lost its depth"
    assert lock._depth == 0 and lock._fd is None
    assert other_thread_attempt(lock) == [("acquired", 1)]
