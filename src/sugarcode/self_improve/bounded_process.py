"""POSIX bounded pipe capture, not host-effect containment or RSS quota."""
from dataclasses import dataclass
import math
import os
import selectors
import signal
import subprocess
import time

OUTPUT_BYTES = 1024 * 1024
TAIL_BYTES = 4000


@dataclass(frozen=True)
class CapturedProcess:
    exit_code: int
    stdout: bytes
    stderr: bytes
    timed_out: bool
    overflow_stream: str | None
    stdout_observed: int
    stderr_observed: int
    max_retained_bytes: int


def _kill_group(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_bounded_process(command, *, timeout_seconds, cwd=None, env=None,
                        output_bytes=OUTPUT_BYTES, tail_bytes=TAIL_BYTES):
    """Consume no more than per-stream cap+1, keep only bounded byte tails.

    Deadline includes inherited pipe lifetime. Always reap direct child. Descendants
    that escape this group and system-level IO stalls are outside the contract.
    """
    if os.name != 'posix':
        raise OSError('bounded native process capture requires POSIX')
    if type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds) or timeout_seconds<=0:
        raise ValueError('timeout must be positive finite number')
    for value in (output_bytes,tail_bytes):
        if type(value) is not int or value<0:
            raise ValueError('capture byte limits must be nonnegative exact ints')
    deadline=time.monotonic()+timeout_seconds
    child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           cwd=cwd,env=env,start_new_session=True,bufsize=0)
    tails={'stdout':bytearray(),'stderr':bytearray()}
    counts={'stdout':0,'stderr':0}
    overflow=None;timed=False;peak=0
    try:
        with selectors.DefaultSelector() as selector:
            for stream,name in ((child.stdout,'stdout'),(child.stderr,'stderr')):
                os.set_blocking(stream.fileno(),False)
                selector.register(stream,selectors.EVENT_READ,name)
            while selector.get_map():
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    timed=True;_kill_group(child);break
                for key,_ in selector.select(timeout=remaining):
                    name=key.data
                    budget=output_bytes-counts[name]+1
                    try:
                        chunk=os.read(key.fileobj.fileno(),min(65536,budget))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    counts[name]+=len(chunk)
                    # Capture budget bound independent of emitted volume. Chunk
                    # allocation <=64KiB, persistent diagnostic rings <=2*tail.
                    if tail_bytes:
                        tails[name].extend(chunk[-tail_bytes:])
                        if len(tails[name])>tail_bytes:
                            del tails[name][:-tail_bytes]
                    peak=max(peak,sum(map(len,tails.values())))
                    if counts[name]>output_bytes:
                        overflow=name;_kill_group(child);break
                if overflow:break
            # Pipes may close before process exits. Same deadline covers wait.
            if not timed and not overflow:
                remaining=deadline-time.monotonic()
                try:child.wait(timeout=max(0,remaining))
                except subprocess.TimeoutExpired:timed=True;_kill_group(child)
        child.wait()
        return CapturedProcess(child.returncode,bytes(tails['stdout']),bytes(tails['stderr']),
                               timed,overflow,counts['stdout'],counts['stderr'],peak)
    except BaseException:
        _kill_group(child);child.wait();raise
    finally:
        child.stdout.close();child.stderr.close()
