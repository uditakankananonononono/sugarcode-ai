# Approval writes reject unsupported JSON before opening state

Base: published 1328d05f668504231338ed9ee9d0d0fe9e708387. Complements stored-read
repair e5ac17dc, does not replace its history or authenticity limits.

ManualApprovalGate._save snapshots the COMPLETE prospective gate object using
snapshot_json, then encodes with allow_nan=False before write_text. Unsupported
values, NaN/Infinity, cycles, non-string keys, subclasses, depth above 64 and
expanded value count above 10,000 fail with InvalidApprovalState. Encoder
ValueError/TypeError/RecursionError, including active interpreter integer-limit
failures, use that type and retain original cause. No invalid serialization
opens/truncates the file. Subsequent valid request/decision remains usable.

Exact builtin tuple becomes a JSON array; shared acyclic objects expand and count
against the budget. Arbitrary conversion/deepcopy methods are not invoked. Caller
mutation after request returns does not change persisted payload. No concurrent-
caller snapshot isolation guarantee or byte-sized cap.

Important compatibility limit: the budget applies to ALL stored approval records
plus the new operation, not just the request payload. A historical file larger
than 10,000 expanded values can still be read by the preceding reader, but any
save is refused unchanged. A gate growing to that boundary needs a separately
designed retention/migration policy; this unit neither deletes old approvals nor
invents one. No arbitrary lifetime/scalability claim.

Bad fresh payloads no longer cause the earlier NaN self-inflicted lockout.
Already-poisoned history still requires manual repair; no migration. File remains
manual unauthenticated state, complete request/status schema not enforced.
IO/MemoryError/OverflowError not normalized; filesystem write failure/crash may
still truncate valid serialized state. No atomic-save/cross-process-lock promise.

Builder: 14 new cases PASS; exact same test file on published base 13 FAIL/1 PASS.
Broader self_improve + shared-layer + router-asset selection 198 PASS, no skips
(184 prior +14 new), not an independent gate/full configured-suite/CI result.
Archive includes all selected test files and src/sugarcode for reviewer replay.

## Independent verdict and accumulating-history ceiling

Independent verdict relayed 2026-10-10: VERIFIED for write-boundary scope and
closing new-write NaN self-lockout. Verifier reproduced 14 new PASS, archived
self_improve 181 PASS, exact base reversal 13 FAIL/1 PASS and hostile-value probes.
Broader 198 includes 17 builder-receipt-only cases; archive omitted instinct_models
required by those tests. No independent whole-configured-suite claim.

LARGEST PRACTICAL RESIDUE: the whole-state 10,000-value budget accumulates with
approval history. Eventually EVERY save, including deciding existing requests,
can be refused until manual history editing. This is a lifetime accumulating-
history ceiling, not merely a single-large-payload limit. No automatic retention,
compaction or migration exists; define one separately before scaling this gate.

"Invalid decided_by" means unsupported/non-encodable values only. None is
accepted and becomes JSON null; no string/person-identity validation is claimed.
Missing IDs/nonobject records retain KeyError/TypeError edges. Other JSON readers,
non-atomic persistence and authority/schema limitations remain unchanged.
