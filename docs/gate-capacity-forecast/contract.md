# Proposed report schema - not installed API

Base: `6e1a42145e529d50751ec3b5cedc6d6ff3105f60`.
Provenance: product `src/sugarcode/self_improve/gate.py:77-142`,
`json_values.py:19-51`, `capped_readers.py:12`, `approval_schema.py:81-128`.
Reference implementation exists INSIDE TESTS ONLY, never in package code.

## Inputs

- Explicit caller-owned source bytes, SHA256 and synthetic/private classification.
  Only synthetic fixtures are used in this delta. Raw bytes distinguish compact
  and pretty representations of the same data. No implicit live file lookup.
- Exact operation: request with complete envelope and explicit unique generated ID,
  or decision with existing ID, approved/rejected status, exact timestamp and actor.
- Declared bounds for ID alphabet/length/uniqueness, payload nested shapes/strings,
  actor null/string/container semantics, timestamp types and serialized length.
  Missing bounds produce uncertainty, never estimated random-average capacity.
- auto_approve flag, necessary for approved-but-unrecorded request envelopes.
- Immutable base SHA and environment/serializer description.

## Outputs

- `base`, `source_sha256`, `raw_bytes`, `raw_headroom`.
- `baseline`: expanded_values, depth (root zero), encoded_bytes, value_headroom,
  depth_headroom, encoded_headroom; or unavailable_reason if baseline snapshot
  validation/serialization refuses. Do not confuse a failed baseline save with
  a failed raw read or with all possible repair writes.
- `prospective`: admitted + counts/headroom; or refusal reason and provenance.
  Actual gate error is separately recorded by auditor tests: class and cause.
  Reasons distinguish raw_file_bytes, duplicate_key, nonfinite, expanded_values,
  depth, cycle, custom_input, key_type, schema reason codes, encoded_file_bytes,
  invalid operation/status/ID. I/O failures are outside the mathematical forecast.
- `live_usage: UNKNOWN`; `archive_eligibility: 0`.
- uncertainty list: exact synthetic shapes only; environment/serializer assumptions;
  ID collision policy; missing or interval bounds; I/O/locking/durability excluded.

## Definitions and limitations

Capacity is admission, not authority/authentication, clinical validity, binding,
write completion or installed recovery policy. The raw `_load` boundary and the
full `_save` boundary are separate (`gate.py:77-99`). Source refusal carries stage=source and gate.py:77-88 provenance.
Single-fault probes permit reason comparison; mixed-domain reference reason is
diagnostic, not guaranteed product first-error priority across entry order. Reference measure visits can distinguish depth/count;
product wraps both with one InvalidTelemetryValue size/depth message.

Positive value/byte headroom alone does not approve a prospective operation.
Decision envelopes must be rebuilt with timestamp/actor fields before counting.
Copy-on-write replaces old root/record nodes; it does not retain old snapshots
as additional children. Any remaining alias within resulting state counts each
expanded occurrence (`json_values.py:15-16,35-49`).

"N more" is allowed only for a fully specified repeated shape with bounded,
noncolliding generated IDs and explicit timestamp/actor serialization assumptions.
Test fixtures select exact values, a degenerate declared range, not general ranges.
No count under unspecified strings or unconstrained payloads is supplied.
Forecast computation can itself be bounded by traversal refusal; unreadable or
unmeasurable input is not a capacity success. No cross-process containment claim.

## Prep delivery and validation

New docs and one test file only. No product edits or reference package/API module.
Auditor must execute comparisons against real _load/_save/request/decide in isolated
synthetic temp directories, inspect cause chains, execute wrong-reference mutations
and review acceptance coverage before landing. Mutant sentinels in the authored
test file distinguish key-count/dedup/UTF8/indent/sort variants; they do not establish
an executed mutation score. No archive/delete/TTL/cap raise or reserve installed.

Repair scope: source refusal is returned rather than thrown. A byte source that
fails raw admission/strict decode supplies baseline unavailable_reason and a
prospective refusal; it never attempts operation simulation. Baseline unsavable
state can be repaired by UUID collision replacement in actual request code;
no baseline error is a universal write-impossibility proof. Collision is not a
safe recovery recommendation or archive authority. Bundle transports HEAD only;
explicit prerequisite and commit hash establish delta identity, not branch label.
Actual mutation reproduction and unchanged oracle checks are in report/test file.
