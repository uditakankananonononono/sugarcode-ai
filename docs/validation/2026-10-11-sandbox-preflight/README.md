# Child runtime preflight - 2026-10-11

Separate follow-up to the 58-failure diagnosis. Runtime behavior now distinguishes an unavailable test runner from a rejected candidate.

Both SandboxRunner and IsolatedRunner check `import pytest` using the same interpreter and environment used by their child test process. The contained runner performs its dependency check inside the existing bubblewrap mounts and namespaces with `-I`. There is no user-site fallback or weakened isolation. The check occurs after source admission, before candidate files are written, and before candidate execution. It uses bounded output (4 KiB per stream), a 5-second deadline, and a fixed diagnostic that does not expose arbitrary child stderr.

A failed import, startup error, timeout or output overflow raises `SandboxEnvironmentUnavailable` with installation guidance. The engine records `sandbox_environment_unavailable` with a fixed reason and propagates that exception. It does not label the candidate rejected by tests or quietly return an empty proposal report. Normal passing, failing, output-limited and timed-out candidate runs retain their existing SandboxResult mapping. Empty preflight workspaces are removed even when keep_workdirs is requested.

Verification in the existing Python 3.10.12 / pytest 9.1.1 venv:

- Selected new regression suite: 11 passed, 0 skipped, 0 failed (0.45s).
- Full self_improve suite: 1,851 passed, 13 xfailed, 0 failed (43.18s).
- Real user-site-only pytest fixture with child venv lacking pytest, both scrubbed and -I semantics.
- Real bubblewrap containment with a child runtime lacking pytest.
- No candidate files or candidate process on refusal; containment refusal still raises IsolationUnavailable.
- Engine propagation, cleanup with keep_workdirs, startup/import/timeout/overflow refusals and bounded probe arguments.

Commands: `PYTHONPATH=$PWD/src /tmp/sugar-build-venv/bin/python -m pytest -q -p no:cacheprovider tests/self_improve/test_runtime_preflight.py`, then the same command with `tests/self_improve`.

The previously documented full configured-suite counts remain tied to a9b532d before this follow-up. The whole configured suite was not rerun after this runtime change; this receipt reports its actual scope only. The preflight imports trusted installed pytest but does not collect tests or load pytest plugins. It adds a separate bounded startup check, not a hostile-runtime security guarantee.
