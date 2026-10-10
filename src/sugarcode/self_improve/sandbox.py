"""Subprocess sandbox: run a candidate feature's tests in isolation.

The candidate and its tests are written to a fresh temp dir and executed
with a scrubbed environment and a hard timeout. pytest is the runner.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .bounded_process import run_bounded_process
from .source_admission import admit_candidate_text, PRODUCTION_SOURCE_LIMITS
from .plans import Candidate


@dataclass(frozen=True)
class SandboxResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    workdir: str = ""
    output_limit_exceeded: bool = False
    output_limit_stream: str | None = None


class SandboxRunner:
    def __init__(self, *, timeout_seconds: float = 120.0, keep_workdirs: bool = False) -> None:
        self.timeout_seconds = timeout_seconds
        self.keep_workdirs = keep_workdirs

    @staticmethod
    def _scrubbed_env() -> dict[str, str]:
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0",
               "HOME": tempfile.gettempdir(), "PYTHONDONTWRITEBYTECODE": "1"}
        for var in ("SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL"):
            if var in os.environ:
                env[var] = os.environ[var]
        return env

    def run(self, candidate: Candidate) -> SandboxResult:
        snapshot = admit_candidate_text(candidate.code, candidate.test_code, limits=PRODUCTION_SOURCE_LIMITS)
        workdir = Path(tempfile.mkdtemp(prefix="sugarcode-si-sandbox-"))
        (workdir / "feature.py").write_bytes(snapshot.code.content)
        (workdir / "test_feature.py").write_bytes(snapshot.tests.content)
        start = time.monotonic()
        try:
            proc = run_bounded_process(
                [sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider", str(workdir)],
                timeout_seconds=self.timeout_seconds, env=self._scrubbed_env(), cwd=str(workdir))
            duration = time.monotonic() - start
            stdout = proc.stdout.decode("utf-8", errors="replace")
            stderr = proc.stderr.decode("utf-8", errors="replace")
            if proc.timed_out:
                stderr = f"timed out after {self.timeout_seconds}s"
            elif proc.overflow_stream is not None:
                reason = f"output byte limit exceeded on {proc.overflow_stream}"
                stderr = reason + "\n" + stderr[-3800:]
            return SandboxResult(
                passed=proc.exit_code == 0 and not proc.timed_out and proc.overflow_stream is None,
                exit_code=-1 if proc.timed_out else proc.exit_code,
                stdout=stdout, stderr=stderr, duration_seconds=round(duration, 3),
                timed_out=proc.timed_out,
                workdir=str(workdir) if self.keep_workdirs else "",
                output_limit_exceeded=proc.overflow_stream is not None,
                output_limit_stream=proc.overflow_stream)
        finally:
            if not self.keep_workdirs:
                import shutil
                shutil.rmtree(workdir, ignore_errors=True)
