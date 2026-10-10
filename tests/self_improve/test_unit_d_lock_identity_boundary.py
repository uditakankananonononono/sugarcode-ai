"""UNIT D design-only boundary canaries. Authored NOT RUN; synthetic state only."""
import multiprocessing as mp
import os
from pathlib import Path

import pytest
from sugarcode.self_improve import state_lock as sl

TIMEOUT = 0.15
WATCHDOG = 10


def require_posix():
    if sl.fcntl is None or not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("POSIX locking capability absent; boundary NOT VERIFIED")


def attempt_worker(path, pipe):
    try:
        lock = sl.shared_state_lock(path, timeout=TIMEOUT)
        pipe.send(("ready", lock.identity))
        assert pipe.recv() == "go"
        try:
            with lock:
                info = os.fstat(lock._fd)
                pipe.send(("acquired", info.st_dev, info.st_ino))
        except sl.StateLockTimeout:
            pipe.send(("timeout",))
    except BaseException as exc:
        pipe.send(("error", type(exc).__name__, str(exc)))
    finally:
        pipe.close()


def receipt(pipe):
    assert pipe.poll(WATCHDOG), "child did not produce receipt"
    return pipe.recv()


def finish(process):
    process.join(WATCHDOG)
    assert not process.is_alive(), "child did not exit"
    assert process.exitcode == 0


def stop(process, pipe):
    if process.is_alive():
        process.terminate()
        process.join(WATCHDOG)
    pipe.close()


def spawn_attempt(path):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe()
    process = ctx.Process(target=attempt_worker, args=(str(path), child))
    process.start()
    child.close()
    try:
        assert receipt(parent)[0] == "ready"
    except BaseException:
        stop(process, parent)
        raise
    return process, parent


@pytest.mark.parametrize("alias_kind", ["same", "dot", "symlink_ancestor", "final_symlink"])
def test_canonical_alias_uses_same_pool_object_and_reentrant_depth(tmp_path, alias_kind):
    real = tmp_path / "real"
    real.mkdir()
    path = real / "state.json"
    path.write_bytes(b"{}")
    if alias_kind == "same":
        alias = path
    elif alias_kind == "dot":
        alias = real / ".." / "real" / "state.json"
    elif alias_kind == "symlink_ancestor":
        link = tmp_path / "alias"
        link.symlink_to(real, target_is_directory=True)
        alias = link / "state.json"
    else:
        alias = tmp_path / "alias.json"
        alias.symlink_to(path)
    a = sl.shared_state_lock(path, timeout=TIMEOUT)
    b = sl.shared_state_lock(alias, timeout=TIMEOUT)
    assert a is b
    assert a.identity == str(path.resolve())
    require_posix()
    with a:
        with b:
            assert a._depth == 2


def test_same_key_different_timeout_refuses(tmp_path):
    path = tmp_path / "state.json"
    sl.shared_state_lock(path, timeout=TIMEOUT)
    with pytest.raises(ValueError, match="same lock timeout"):
        sl.shared_state_lock(path, timeout=TIMEOUT * 2)


def test_parent_held_sidecar_child_times_out_before_parent_release(tmp_path):
    require_posix()
    path = tmp_path / "state.json"
    held = sl.shared_state_lock(path, timeout=TIMEOUT)
    with held:
        process, pipe = spawn_attempt(path)
        try:
            pipe.send("go")
            assert receipt(pipe) == ("timeout",)
            assert held._depth == 1 and held._fd is not None
            finish(process)
        finally:
            stop(process, pipe)


def test_hardlinked_json_names_have_different_locks_and_can_acquire(tmp_path):
    require_posix()
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_bytes(b"{}")
    os.link(a, b)
    assert a.stat().st_ino == b.stat().st_ino
    first = sl.shared_state_lock(a, timeout=TIMEOUT)
    second = sl.shared_state_lock(b, timeout=TIMEOUT)
    assert first is not second and first.identity != second.identity
    with first:
        process, pipe = spawn_attempt(b)
        try:
            pipe.send("go")
            result = receipt(pipe)
            assert result[0] == "acquired", result
            old = os.fstat(first._fd)
            assert result[1:] != (old.st_dev, old.st_ino)
            finish(process)
        finally:
            stop(process, pipe)


@pytest.mark.parametrize("operation", ["unlink", "replace"])
def test_noncooperating_sidecar_change_allows_second_inode_lock(tmp_path, operation):
    require_posix()
    path = tmp_path / "state.json"
    held = sl.shared_state_lock(path, timeout=TIMEOUT)
    with held:
        original = os.fstat(held._fd)
        if operation == "unlink":
            held.sidecar.unlink()
        else:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"")
            os.replace(replacement, held.sidecar)
        process, pipe = spawn_attempt(path)
        try:
            pipe.send("go")
            result = receipt(pipe)
            assert result[0] == "acquired", result
            assert result[1:] != (original.st_dev, original.st_ino)
            assert held._depth == 1
            finish(process)
        finally:
            stop(process, pipe)


def test_ancestor_alias_swap_changes_fresh_key_not_cached_identity(tmp_path):
    a, b, link = tmp_path / "a", tmp_path / "b", tmp_path / "alias"
    a.mkdir()
    b.mkdir()
    (a / "state.json").write_bytes(b"{\"which\":\"a\"}")
    (b / "state.json").write_bytes(b"{\"which\":\"b\"}")
    link.symlink_to(a, target_is_directory=True)
    caller_path = link / "state.json"
    old = sl.shared_state_lock(caller_path, timeout=TIMEOUT)
    link.unlink()
    link.symlink_to(b, target_is_directory=True)
    fresh = sl.shared_state_lock(caller_path, timeout=TIMEOUT)
    assert old.identity == str(a / "state.json")
    assert fresh.identity == str(b / "state.json")
    assert old is not fresh
    assert caller_path.read_bytes() == (b / "state.json").read_bytes()


def fork_worker(path, inherited, pipe):
    try:
        try:
            with inherited:
                pipe.send(("error", "inherited acquired"))
                return
        except sl.StateLockUnavailable:
            pipe.send(("inherited-refused",))
        fresh = sl.shared_state_lock(path, timeout=TIMEOUT)
        pipe.send(("reset", fresh is not inherited, sl._pool_pid == os.getpid(),
                   len(sl._pool), fresh._depth))
        try:
            with fresh:
                pipe.send(("error", "fresh bypassed parent"))
        except sl.StateLockTimeout:
            pipe.send(("fresh-timeout",))
    except BaseException as exc:
        pipe.send(("error", type(exc).__name__, str(exc)))
    finally:
        pipe.close()


def test_fork_inherited_refusal_fresh_pool_reset_and_parent_contention(tmp_path):
    require_posix()
    if "fork" not in mp.get_all_start_methods():
        pytest.skip("fork absent; inheritance NOT VERIFIED")
    path = tmp_path / "fork.json"
    held = sl.shared_state_lock(path, timeout=TIMEOUT)
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe()
    with held:
        process = ctx.Process(target=fork_worker, args=(str(path), held, child))
        process.start()
        child.close()
        try:
            assert receipt(parent) == ("inherited-refused",)
            assert receipt(parent) == ("reset", True, True, 1, 0)
            assert receipt(parent) == ("fresh-timeout",)
            assert held._fd is not None and held._depth == 1
            finish(process)
        finally:
            stop(process, parent)


@pytest.mark.parametrize("slow_call", ["open", "fstat"])
def test_deadline_does_not_interrupt_io_or_refuse_immediate_flock_after_it(
    tmp_path, monkeypatch, slow_call
):
    require_posix()
    clock = [100.0]
    original = getattr(sl.os, slow_call)
    def slow(*args, **kwargs):
        clock[0] += 20
        return original(*args, **kwargs)
    monkeypatch.setattr(sl.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(sl.os, slow_call, slow)
    lock = sl.shared_state_lock(tmp_path / "slow.json", timeout=TIMEOUT)
    with lock:
        assert clock[0] == 120.0
        assert lock._depth == 1


def pool_worker(root, pipe):
    try:
        before = len(sl._pool)
        for i in range(32):
            sl.shared_state_lock(Path(root) / f"state-{i}.json", timeout=TIMEOUT)
        after = len(sl._pool)
        again = sl.shared_state_lock(Path(root) / "state-0.json", timeout=TIMEOUT)
        pipe.send(("pool", after - before, len(sl._pool) == after,
                   all(item._fd is None for item in sl._pool.values()), again._depth))
    except BaseException as exc:
        pipe.send(("error", type(exc).__name__, str(exc)))
    finally:
        pipe.close()


def test_pool_keeps_unique_keys_without_eviction_or_open_descriptors(tmp_path):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe()
    process = ctx.Process(target=pool_worker, args=(str(tmp_path), child))
    process.start()
    child.close()
    try:
        assert receipt(parent) == ("pool", 32, True, True, 0)
        finish(process)
    finally:
        stop(process, parent)


@pytest.mark.parametrize("missing", ["fcntl", "O_NOFOLLOW"])
def test_missing_required_platform_capability_fails_closed(tmp_path, monkeypatch, missing):
    if missing == "fcntl":
        monkeypatch.setattr(sl, "fcntl", None)
    else:
        monkeypatch.delattr(sl.os, "O_NOFOLLOW", raising=False)
    lock = sl.shared_state_lock(tmp_path / "unsupported.json", timeout=TIMEOUT)
    with pytest.raises(sl.StateLockUnavailable, match="unavailable"):
        with lock:
            pytest.fail("unlocked fallback")
    assert lock._fd is None and lock._depth == 0


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_nonregular_final_sidecar_refuses(tmp_path, kind):
    require_posix()
    path = tmp_path / "bad.json"
    side = Path(str(path) + ".lock")
    if kind == "symlink":
        target = tmp_path / "target"
        target.write_bytes(b"")
        side.symlink_to(target)
    elif kind == "directory":
        side.mkdir()
    else:
        os.mkfifo(side)
    with pytest.raises(OSError):
        with sl.shared_state_lock(path, timeout=TIMEOUT):
            pytest.fail("unsafe sidecar acquired")


def test_canonical_ancestor_replacement_allows_new_sidecar_inode(tmp_path):
    require_posix()
    directory = tmp_path / "active"
    directory.mkdir()
    path = directory / "state.json"
    held = sl.shared_state_lock(path, timeout=TIMEOUT)
    with held:
        original = os.fstat(held._fd)
        directory.rename(tmp_path / "retired")
        directory.mkdir()
        process, pipe = spawn_attempt(path)
        try:
            pipe.send("go")
            result = receipt(pipe)
            assert result[0] == "acquired", result
            assert result[1:] != (original.st_dev, original.st_ino)
            assert held.identity == str(path) and held._depth == 1
            finish(process)
        finally:
            stop(process, pipe)
