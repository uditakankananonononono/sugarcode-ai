# Approval full-record API and engine binding

Current base2aefa5a (ledger, strict stdout, atomic gate/registry already landed).
Peer J05 v2 helper retained, earlier v1 discarded. Fix7 authored-test fixture
failures: None payload was replaced with default; rollback duplicate payload
argument never reached validator. Corrected fixtures82 PASS, not removed cases.

Manual gate record(id) returns detached snapshot, validates minimal status/object
shape. decision() uses it. Generic request actions/payloads and minimal legacy
status-only reads/decisions remain compatible. New requests validate generic
full envelope; existing full records validate on decide. Known-action payload
semantics enforced at engine activation/rollback only, not arbitrary generic
workflow. Existing minimal legacy record is NOT enough to authorize engine action.

Engine activation additionally binds full record to exact action/module ID/slug/
candidate key/name/kind/code digest/gap signature; proposal approval ID still
must match. Rollback additionally binds exact action/module/feature. Pending/
rejected/unrecorded manual decision refuses. Explicit exact ManualApprovalGate
with _auto is True may use its existing auto-approval shape; custom status-only
gate lacks record API and now fails closed. Full-record custom sources remain
trusted injected Python, not an authentication service. ApprovalGate Protocol
now names record API.

Null decided_by preserved. Nonempty string decider otherwise, exact-int module ID,
finite numeric timestamps, exact envelope fields and known-action payload keys.
Unknown/full legacy schemas not migrated; empty gap signature in known action
refused. Schema matching is NOT human consent/actor attribution/cryptographic
integrity: local editor can fabricate a matching record. Auto mode is trusted
configuration, not verified permission. No atomic gate+registry+ledger transaction,
no cross-process/revoke race closure. F01 postreplace request exception approval_id
and SC-J04 snapshot/history limits preserved. Low-level registry.activate/rollback
remain direct trusted APIs; this boundary applies to ENGINE entry points.

A01 version pin/replay binding NOT integrated yet: rollback is feature-bound but
not bound to active-version-at-request or once-only consumed approval. Report
these separately; do not advertise complete replay/revocation authorization.

Builder selected411 PASS/no skips: prior main310 +82 helper +19 seam cases.
Includes actual generic legacy, auto, status-only custom source, wrong identity/
payload, rollback activation-ID misuse and atomic orphan-ID regressions. Base
seam canaries copied unchanged to2aefa5a detect absent API/binding. Independent
verdict required. Initial merge attempt introduced an IndentationError before
collection; fixed before passing run, no failed probe called green.

Independent verdict VERIFIED engine binding, scoped base canary receipt not rerun.
Verifier independently411PASS plus real authorization/subclass probes. Deliberate
policy effects: status-only manual editor must also write decided_at/decided_by;
ManualApprovalGate subclasses do NOT inherit unrecorded auto-decision bypass
(exact type, not isinstance). Generic legacy read/decide compatibility preserved.
