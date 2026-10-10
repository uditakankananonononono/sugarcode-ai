# File-backed approval JSON read boundary

Candidate base: published ba0eb275f182e77a4f24530b668e3e17f2528df5.
Scope is ManualApprovalGate._load(), not a repository-wide JSON/schema repair.

Stored JSON objects reject repeated decoded keys at every depth, including
Unicode-escaped equivalent names. NaN, Infinity, -Infinity and numeric exponents
that decode to infinity are refused. Top level must be an object; syntax,
conversion and recursion errors raise InvalidApprovalState with original cause.
No invalid file is rewritten by decision(), request() or decide(): each loads
before mutation. A bad row/field blocks the entire file, not a partial return.
Equal names in separate objects remain valid. Normal pending/approved workflows
remain operational in tests.

Not authorization: a local actor can still edit the file to put a well-formed
approved status there. No actor identity/authentication, cryptographic signature,
consent proof, semantic payload match or complete request schema validation.
Statuses and nested request shapes are not validated beyond the JSON boundary;
unknown/missing status keys can still raise KeyError or return unexpected values.

No byte/depth/value-count cap, no cross-process lock, no atomic-save repair,
no migration or containment claim. OSError, MemoryError and OverflowError are not
normalized. Fresh _save still uses the existing permissive encoder: a caller's
nonfinite payload may be persisted and then refused on the next read. This unit
fixes stored-read ambiguity, not every input/write boundary. Other readers are
unchanged. An oversized JSON integer follows the active interpreter conversion
limit; ValueError is typed on read, not a portable magnitude policy.

Builder evidence: 38 new cases PASS. Broader self_improve + shared-layer +
router-asset selection: 184 PASS (146 prior selection +38), no skips. On exact
base, baseline canaries change only the unavailable new error import to generic
ValueError-with-message expectation: 36 FAIL, 2 PASS, with failure due to accepted
bad data, mutation or wrong errors, not an ImportError. This adaptation is in the
review packet; it is not claimed byte-identical test execution on base.
These are builder counts, not independent acceptance/full-suite/CI/spec completion.

## Independent stored-read verdict and next-unit risk

Independent verdict relayed 2026-10-10: VERIFIED for stored-read scope; SCOPED
on counts. Verifier reproduced 38 new PASS, 167 archived self_improve PASS,
and adapted base 36 FAIL/2 PASS. The extra 17 tests in builder's 184 selection
were not archived: shared-layer 10 + router-asset 7, receipt-level only.
Commit/base identity remained archive-unverified; builder verifies publication.

PROMINENT REMAINING RISK: a fresh NaN request payload can SELF-LOCK OUT the gate:
existing _save writes it successfully, then this repaired reader rejects the
whole file until manual repair. Write-side snapshot/allow_nan=False validation
is the next separate unit, not fixed by this stored-read candidate. Unknown IDs
still raise KeyError and nonobject entries TypeError. Engine/wiring fail-closed
caller behavior was not independently tested by this unit.
