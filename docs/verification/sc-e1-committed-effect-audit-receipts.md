# SC-E1: distinguish completed effects from failed audit append

Base 723653cadddca409ad4a5a7ad4caccef7b447aea. A real approved activation
under a synthetic zero-byte ledger budget raised InputLimitExceeded even though
version 1 and its consumed approval were committed. A caller retry then refused
as already consumed. Generic failure hid the operational outcome.

## Installed contract

Engine activate and rollback now raise CommittedEffectAuditError only when their
registry operation returned successfully and the subsequent ledger append raises
an Exception. It carries operation, subject (candidate key or feature), approval_id,
version, outcome, committed=True, retry_safe=False and the logger error as cause.
Normal successful returns and logs are unchanged. No log error is swallowed and
no effect is retried. Rollback outcome retains both prior and resulting version.
The committed flag means the registry operation returned, not power-loss proof.
KeyboardInterrupt/SystemExit and other BaseException cancellation are not wrapped.

Engine dispatch uses an internal registry result/version receipt returned only
after its dispatch counter save succeeds. It thus reports the version actually
executed, not a later reread of whichever version is now active. Public registry
and engine dispatch return values remain unchanged on normal success. If the
engine's subsequent ledger append fails, its typed exception contains small
outcome metadata and the EXACT in-memory result_reference. It never serializes,
snapshots, stringifies or reprs that arbitrary result. This reference is explicitly
non-serializable/non-durable, potentially large, mutable and process-local. Callers
must not treat the exception object as JSON or a safe data-export format. No
result-size bound is claimed. Metadata does not include the arbitrary result.

Registry/counter failures BEFORE that receipt retain existing exception behavior:
execution may already have occurred, so ordinary errors do not imply safe retry.
AtomicDurabilityError and SourcePublicationError stay typed as before, including
uncertain postreplace state. No generic precommit failure is re-labelled committed.

Request/propose/record_gap partial effects, retention, audit repair, cross-file
transactions, undo, automatic recovery, exactly-once host effects and crash
durability remain outside this unit. An exception makes the completed operational
state visible; it does not create missing audit data or undo the operation.

## Verification

New tests execute real approved activation, two-version rollback and feature
execution with ledger-cap, malformed-history and injected IO failures. They assert
exact typed receipts, cause, state/consumption, restart readback and replay refusal.
A feature returning an object with hostile str/repr mutates a synthetic host marker;
receipt preserves it in memory without conversion and marker/counter remain one.
Additional tests keep pre-effect errors, counter-save failure and postreplace
registry durability exceptions outside committed-audit taxonomy. Normal returns
remain unchanged. These are synthetic fault tests, not OS reliability estimates.

Four source mutations killed by assertion oracles: swallowing audit error,
dropping activation outcome, falsely claiming precommit state, retrying dispatch.
Full receipts and source mutation script accompany the package; counts name actual
collected cases. Independent audit and landed-public-tree check required before
completion. No configured-full-suite PASS or clinical/novelty claim is made.

Builder execution record: 17 new cases pass. Full self_improve rerun 1353 PASS,
13 expected XFAIL, zero SKIP. Previous final attempt had 1352 PASS/13 XFAIL/1 FAIL:
existing test_bounded_process::test_same_group_descendant_killed_on_timeout hit
ProcessLookupError when /proc disappeared between exists/read. Failure XML retained,
not deleted or counted as PASS. Exact failing test plus 17 new cases reran 18 PASS;
subsequent full rerun is the 1353/13 result above. No unrelated test was edited.
Independent auditor should check the same failure possibility. Four final mutation
runs: swallow 3 FAIL/14 PASS; drop outcome 3 FAIL/14 PASS; precommit claim 1 FAIL/
16 PASS; dispatch retry 4 FAIL/13 PASS. No collection/setup failure or timeout.
