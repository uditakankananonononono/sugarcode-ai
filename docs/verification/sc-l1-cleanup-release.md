# SC-L1: failed acquisition cleanup releases Python lock depth

Base: 53234d9e0f8343f890560880054383b1568c7580. Scope: the failure
handler in StateLock.__enter__, one synthetic test file, this receipt.
No timeout, identity, fork, platform, sidecar, successful-entry or exit policy
changed. No Unit D test changed.

## Reproduced defect and fix

An injected fstat acquisition error followed by an injected close error after
actually closing the tentative descriptor skipped the Python RLock release.
With the seams restored, another thread using the same pooled object timed out,
although _depth was zero and _fd was None. The owner test thread explicitly
released its stranded RLock. This is injected behavior, not a measured frequency
of real OS close failures.

The descriptor close now runs inside try/finally, whose finally releases the
one Python-lock depth acquired by the failed entry. Close errors still propagate
and retain the acquisition error as exception context. There is no close retry.
If an OS close fails before actually closing, descriptor reclamation is not
promised. The fix concerns Python-lock release only. The original acquisition
exception is re-raised when cleanup succeeds.

## Builder results, not independent verdict

- New file: 5 collected cases, 5 PASS, 0 SKIP. Covers fstat+successful close,
  fstat+close error, flock+close error, missing capability before fd, and success/
  reentrancy with another-thread timeout while held and reacquisition after exit.
- Selected adjacent run: 44 collected cases, 44 PASS, 0 SKIP. Files:
  test_state_lock_cleanup_release.py (5), test_state_lock_integration.py (19),
  test_unit_d_lock_identity_boundary.py (20). This includes existing parent-held
  child contention. It is not a full configured-suite run.
- Three source mutations rejected with assertion failures, no collection error
  or watchdog timeout: original close-before-release (2 FAIL/1 PASS/2 deselected),
  omitted release (3 FAIL/2 deselected), extra release (1 FAIL/2 PASS/2 deselected).
  All mutations ran only the three failed-acquisition cases. The extra-release
  mutation changes the raised exception to RuntimeError and is caught by the
  explicit exception-contract assertion. No mutation survives.
- After restoring source, the 5 new cases passed again. Receipts accompany the
  package. Test watchdogs bound follow-up waiting, not operation performance.
  Synthetic tmp paths only; no live owner state or paid services.

Independent auditor must reproduce against the exact candidate, inspect the
minimal diff and exception contract, and issue a scoped verdict before landing.
No hostile-filesystem containment, cross-file atomicity, real close-fault
reliability, total I/O deadline, pool reclamation or fork repair is claimed.
