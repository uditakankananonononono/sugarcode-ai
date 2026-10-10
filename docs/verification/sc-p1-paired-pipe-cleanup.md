# SC-P1: paired pipe cleanup after injected close failure

Base: 070103312fe2a245deda3d31a9c6406239fb4012. Product scope:
run_bounded_process final pipe-close cleanup only. New synthetic tests and
this receipt accompany the change. No process-group, deadline, output budget,
selector loop, child wait/reap, tail or result-field policy changed.

## Reproduction and contract

Before editing product code, a synthetic real child printed and exited zero.
A stdout proxy delegated the actual close, then raised an injected OSError.
The original sequential final cleanup skipped stderr: stdout closed, stderr
still open, direct child already reaped. The test explicitly closed stderr.

Cleanup now attempts stdout then stderr exactly once each. If stdout close
raises, stderr close is still attempted and the original stdout exception
remains primary even if stderr close also raises. If stdout succeeds and stderr
fails, stderr's exception propagates. A capture error can still be superseded
by a close error, as before. No retry close is introduced. If a close operation
raises before actually closing, freeing that descriptor is not promised.
The paired-attempt invariant is not a real OS close-reliability measurement.

## Builder evidence, independent verdict pending

5 new cases PASS/0 SKIP: neither close fails, stdout fails, stderr fails, both
fail, and selector-registration capture error plus stdout close failure. Real
children and proxies are used, and underlying streams actually close before
injections. Exception identity, capture-error context, direct-child reaping,
paired call counts and underlying stream state are asserted. A test finally
cleans up children/streams even under failing source mutations.

46 selected cases PASS/0 SKIP: new paired-cleanup tests plus
 test_bounded_process.py, test_sandbox_output_caps.py,
 test_isolated_output_parity.py and test_sandbox.py. These are selected native/
isolated capture and sandbox regressions, not a full configured-suite run.

Source mutation reruns using the same five new cases:
- Original/base sequential cleanup: 3 assertion FAIL, 2 PASS.
- Omit stderr close: 5 assertion FAIL.
- Nested finally with reversed both-error precedence: 1 assertion FAIL, 4 PASS.
No collection/setup failure or harness timeout killed these mutants. Candidate
source restored before the 46-case run. Mutation script and full receipts travel
with the packet. Harness timeouts are watchdogs, not performance evidence.

Independent auditor must inspect the exact minimal diff, rerun the cases and
mutations, verify exception precedence and issue a scoped verdict before landing.
No claim about OS close-fault rates, hostile descendants, system-level IO stalls,
kill/selector cleanup failures, hard resource containment or full-suite success.
Synthetic state only. No owner live files, services or paid routes used.
