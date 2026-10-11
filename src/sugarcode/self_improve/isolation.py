"""Opt-in Linux bubblewrap runner. Refuses unavailable containment; no fallback.

Only the current trusted Python runtime and system libraries are read-only
mounted. A private temporary work directory is writable. Network, PID, IPC,
UTS and user namespaces are isolated. Not a hostile-kernel security boundary.
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from .bounded_process import run_bounded_process
from .source_admission import admit_candidate_text, PRODUCTION_SOURCE_LIMITS
from .sandbox import SandboxResult
from .runtime_preflight import require_pytest, SandboxEnvironmentUnavailable

class IsolationUnavailable(RuntimeError):
    pass

class IsolatedRunner:
    def __init__(self, *, timeout_seconds=120., bwrap=None):
        if timeout_seconds <= 0:
            raise ValueError('timeout must be positive')
        self.timeout_seconds = timeout_seconds
        self.bwrap = bwrap or shutil.which('bwrap')

    def _command(self, work):
        if not self.bwrap or not Path(self.bwrap).is_file():
            raise IsolationUnavailable('bubblewrap executable unavailable')
        cmd=[self.bwrap, '--tmpfs','/tmp','--tmpfs','/home', '--unshare-all', '--die-with-parent', '--new-session',
             '--cap-drop','ALL']
        roots={Path('/usr'),Path('/lib'),Path('/lib64'),
               Path(sys.prefix),Path(sys.base_prefix),Path(sys.executable).resolve().parent.parent}
        if Path(sys.executable).is_symlink():
            target=Path(os.readlink(sys.executable))
            if target.is_absolute():roots.add(target.parent.parent)
        # Runtime roots are trusted installation locations, not owner data.
        # Reject broad mounts rather than exposing an entire home/tmp tree.
        for root in sorted(roots,key=str):
            if root in (Path('/'),Path('/home'),Path('/home/sandbox'),Path('/tmp')):
                raise IsolationUnavailable('unsafe Python runtime mount root')
            if root.exists():cmd += ['--ro-bind',str(root),str(root)]
        cmd += ['--proc','/proc','--dev','/dev','--bind',str(work),'/work','--chdir','/work',
                '--clearenv','--setenv','PATH','/usr/bin',
                '--setenv','HOME','/tmp','--setenv','PYTHONHASHSEED','0',
                '--setenv','PYTHONDONTWRITEBYTECODE','1',
                '--setenv','PYTEST_DISABLE_PLUGIN_AUTOLOAD','1']
        return cmd

    def run(self,candidate):
        snapshot=admit_candidate_text(candidate.code,candidate.test_code,limits=PRODUCTION_SOURCE_LIMITS)
        start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='sugarcode-isolated-') as tmp:
            work=Path(tmp)
            cmd=self._command(work)
            # Verify namespace/mount setup before running any candidate code.
            try:
                probe=subprocess.run(cmd+[sys.executable,'-I','-c','pass'],
                                     capture_output=True,timeout=5)
            except (OSError,subprocess.TimeoutExpired) as exc:
                raise IsolationUnavailable('containment probe failed') from exc
            if probe.returncode:
                raise IsolationUnavailable('containment probe refused: '+probe.stderr.decode(errors='replace')[-1000:])
            require_pytest(cmd+[sys.executable, '-I'])
            (work/'feature.py').write_bytes(snapshot.code.content)
            (work/'test_feature.py').write_bytes(snapshot.tests.content)
            # Limit ordinary resource use in the child before pytest. Hard
            # limits cannot be raised by the candidate after capabilities drop.
            launcher="import resource,os,sys; resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912)); resource.setrlimit(resource.RLIMIT_CPU,(10,10)); resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576)); resource.setrlimit(resource.RLIMIT_NOFILE,(64,64)); os.execv(sys.executable,[sys.executable,'-m','pytest','-q','-x','--no-header','-p','no:cacheprovider','/work'])"
            proc=run_bounded_process(cmd+[sys.executable,'-I','-c',launcher],
                                     timeout_seconds=self.timeout_seconds)
            stdout=proc.stdout.decode('utf-8',errors='replace')
            stderr=proc.stderr.decode('utf-8',errors='replace')
            if proc.overflow_stream is not None:
                stderr=f"output byte limit exceeded on {proc.overflow_stream}\n"+stderr[-3800:]
            return SandboxResult(proc.exit_code==0 and not proc.timed_out and proc.overflow_stream is None,
                                 proc.exit_code,stdout,stderr,round(time.monotonic()-start,3),
                                 proc.timed_out, output_limit_exceeded=proc.overflow_stream is not None,
                                 output_limit_stream=proc.overflow_stream)
