# SC-S1: status polling does not consume audit capacity

Base 842e055ed01695f62582c4b0f0327a2944d24f70. Reproduced real engine
with two gap events: successive status calls increased ledger counts 3 then 4,
bytes 258 -> 388 -> 518, because status invoked logged detect_gaps. The service
mixin delegates this status path. Polling therefore consumed finite log capacity.

Status now reads events once, registry once and ledger once. Gap computation
uses the already-read events through an internal detector computation method.
Covered-gap filtering uses the same single registry state's all-version features
and proposed/activated proposals, matching covers_gap's existing policy. No log
is appended. Explicit detect_gaps and run_cycle retain gap_detected logging.
Ordinary detector.detect returns the same computed results and still reads store.
Status fields and mixin API are unchanged.

The three state reads are independent, not a cross-file atomic/coherent snapshot.
Concurrent cooperating writes can occur between them. No global lock is added.
Read APIs may create stable advisory sidecars, per SC-J6, so filesystem sidecar
creation is not excluded by the no-state-rewrite claim. Invalid ledger/registry/
event history still refuses rather than returning a fabricated healthy status.
No deletion, retention, cap change, capacity relief or audit suppression.

Builder: 7 new cases PASS; full self_improve 1360 PASS, 13 expected XFAIL, zero
SKIP. Repeated engine/mixin reads and restart leave event/ledger/registry/gate
bytes unchanged and assert zero _log calls. Exact-full valid ledger is readable;
malformed ledger still refuses. Proposed/activated gaps remain filtered. Explicit
detection and run_cycle(max_new=0) keep expected audit events. A read-count oracle
requires exactly one event, registry and ledger read each.

Four source mutations killed by assertions: logged status (5 FAIL/2 PASS),
skipped filter (2 FAIL/5 PASS), fake zero ledger count (4 FAIL/3 PASS), omitted
explicit detection log (1 FAIL/6 PASS). No collection/setup failure or timeout.
Full receipts and source mutation script accompany the package. Synthetic paths
only, no live owner state/network/paid routes. Independent verdict required;
no configured-full-suite PASS, full production readiness or atomic status claim.
