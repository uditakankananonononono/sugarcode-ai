"""Path-shared, reentrant cooperating POSIX lock on a stable sidecar.

Advisory only: direct editors/noncooperating writers are not contained.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import stat
import threading
import time

try:
    import fcntl
except ImportError:
    fcntl = None


class StateLockUnavailable(OSError):
    pass


class StateLockTimeout(TimeoutError):
    pass


_pool_guard = threading.Lock()
_pool: dict[str, 'StateLock'] = {}
_pool_pid = os.getpid()


def shared_state_lock(path: Path | str, *, timeout: float = 5.0) -> 'StateLock':
    global _pool, _pool_pid, _pool_guard
    # Child must not inherit a parent's acquired Python RLock/descriptor state.
    if os.getpid() != _pool_pid:
        for item in _pool.values():
            if item._fd is not None:
                os.close(item._fd)
        _pool, _pool_guard, _pool_pid = {}, threading.Lock(), os.getpid()
    key = str(Path(path).resolve())
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('lock timeout must be positive finite number')
    with _pool_guard:
        if key not in _pool:
            _pool[key] = StateLock(key, timeout)
        elif _pool[key].timeout != timeout:
            raise ValueError('same state path requires the same lock timeout')
        return _pool[key]


class StateLock:
    def __init__(self, key: str, timeout: float):
        self.identity = key
        self.timeout = timeout
        self.sidecar = Path(key + '.lock')
        self._thread_lock = threading.RLock()
        self._depth = 0
        self._fd: int | None = None
        self._pid = os.getpid()

    def __enter__(self) -> 'StateLock':
        if self._pid != os.getpid():
            raise StateLockUnavailable('inherited state object must be reconstructed after fork')
        deadline = time.monotonic() + self.timeout
        if not self._thread_lock.acquire(timeout=self.timeout):
            raise StateLockTimeout('state thread lock timed out')
        if self._depth:
            self._depth += 1
            return self
        fd = None
        try:
            if fcntl is None or not hasattr(os, 'O_NOFOLLOW'):
                raise StateLockUnavailable('POSIX advisory state locking unavailable')
            fd = os.open(self.sidecar, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW |
                         os.O_NONBLOCK | getattr(os, 'O_CLOEXEC', 0), 0o600)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise StateLockUnavailable('state lock sidecar must be regular')
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise StateLockTimeout('state advisory lock timed out')
                    time.sleep(min(0.01, max(0, deadline-time.monotonic())))
            self._fd, self._depth = fd, 1
            return self
        except BaseException:
            if fd is not None:
                os.close(fd)
            self._thread_lock.release()
            raise

    def __exit__(self, *exc) -> None:
        self._depth -= 1
        try:
            if self._depth == 0:
                fd, self._fd = self._fd, None
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)
        finally:
            self._thread_lock.release()
