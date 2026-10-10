# UNIT A: approval-ID collision and envelope continuity (PREP-NORUN report)

Status: report plus authored tests only. Tests NOT RUN. No product code changed. Base
6e1a42145e529d50751ec3b5cedc6d6ff3105f60 (verified to resolve in a fresh public clone).
A report is not a repair; the policies below are proposals needing owner-approved
implementation and independent audit.

## What the base does (gate.py lines 101-122 at the base)

`request()` builds `approval_id = f"si-{uuid4().hex[:12]}"` (48 random bits), then under the
shared gate lock loads the file and runs `data[approval_id] = {...}`. There is no membership
check. If the key already exists, the stored value is replaced whole, whatever it held. The new
record is validated, then saved atomically. Nothing in `request()` validates OTHER entries, so
a non-dict or corrupt existing entry is also replaced silently. The engine writes the returned
ID into the registry proposal (`set_proposal_approval`), and consumption is keyed
`sha256([gate_identity, approval_id])` in the registry (`approval_consumption.py`), so the
registry and gate agree only on the ID string.

## Collision-state matrix (existing entry at the drawn ID, then a second `request()`)

| Existing entry | Base result | Consequence |
|---|---|---|
| pending | replaced by new pending record | first request and its payload/summary lost; the person deciding sees the second request under the first's ID; the engine proposal for the first now points at a foreign payload |
| approved, unconsumed | replaced by pending (or approved if the gate is auto) | human approval silently revoked, or an auto gate re-approves; decided_at/decided_by lost |
| rejected | replaced by pending (or approved on an auto gate) | rejection reopened; an auto gate can turn a rejected ID into approved with no human decision |
| approved and consumed | replaced; registry consumption record untouched | gate history (original payload, decided_by, decided_at, requested_at) lost. Engine commit still refuses: same-payload overwrite gives "already consumed" from the registry; different-payload overwrite gives the J05 "binding mismatch". The new request can never be committed (dead request) |
| auto-approved (approved, decided_at null) | replaced | as approved/pending above |
| non-dict or malformed entry | replaced by valid record | masks stored corruption that `record()` would have refused |
| legacy minimal entry (e.g. only `status`) or non-`si-` key | only the exact same key can be hit; `si-` IDs never equal other formats | legacy IDs not at risk unless equal strings |

Engine linkage: the binding in `engine.activate/rollback` (J05 envelope plus A01 pin) refuses
a replaced record whose payload/action/module differs, so a cross-payload overwrite is mostly
caught at commit time, not at request time. It is NOT caught when the payload is identical, and
the J05 envelope says nothing about gate history. Consumption protects commit-once, not history.

## Options (all proposals)

1. Membership check plus bounded retry (recommended for review). Under the existing gate lock,
   after loading the current file, redraw the 12-hex prefix while the key is present, up to a
   cap (proposal: 8), then raise before any write (proposal: `InvalidApprovalState`, message
   "approval id allocation exhausted; state unchanged"). The membership check is what prevents
   overwrite; redrawing is only how a free ID is found. Keeps ID shape and every caller.
   Limits: sees only keys in the current gate file. An ID removed from the gate file by retention
   or a restored old file can be drawn again while its consumption record remains in the
   registry (safe, the commit still refuses, but the new request is dead). Checks the file the
   lock covers; a non-cooperating editor is out of scope. The cap and exception type are choices.
2. Full UUID (`si-` plus 32 hex). Lowers repeat odds but is probability, not a guarantee, and
   changes the ID length/shape (nothing in the repo parses it; `si-forged`/`si-abc` fixtures
   use arbitrary strings). Without a membership check it still overwrites on a repeat, so it
   should be combined with option 1, not substituted for it.
3. Monotonic IDs (e.g. max existing numeric suffix + 1). Deterministic and collision-free while
   the file is intact, but needs a stored counter or derives from existing keys. A counter key
   in the gate file breaks the "every top-level key is a record" reader assumption and the
   retention plan helper; deriving from existing keys can reuse a number after pruning or
   restore, which re-arms the consumed-ID problem above. IDs become guessable (no authentication
   is claimed anywhere, so this is neutral but should be said). Larger format change.

No option fixes cross-store reuse by itself. Possible follow-up (unresolved, not proposed as
done): let the engine refuse a proposal ID that already has a registry consumption record
before `set_proposal_approval`, since only the engine sees both stores.

## Failure behavior that must stay as is

- Request failure before replace leaves the file unchanged (serialization error: "state unchanged").
- Finite size cap: `InputLimitExceeded` before replace; unchanged by the collision check.
- Post-replace directory-sync failure raises `AtomicDurabilityError` with `approval_id` set to
  the ID actually written; state has landed, blind retry not safe. With retry the reported ID
  must be the redrawn one, not the colliding one.
- `engine.propose` saves the registry proposal before calling the gate, so a failed `request()`
  leaves a proposal without an approval ID (unchanged by any option).

## Tests: tests/self_improve/test_approval_id_collision_unit_a.py (authored, NOT RUN)

- Scripts `gate.uuid4` prefixes and `gate.time.time`; temp files only; detects overwrite by
  comparing stored records and the file's key set, not ID lengths.
- `TestBaseCollisionCharacterization` and `TestBaseConsumedIdOverwrite`: expected PASS on the
  base; they document the overwrite and, for the consumed case, history loss together with the
  engine still refusing. They are meant to start failing once a repair lands (replace them then).
- `TestNoOverwriteDesired`: against the real gate each case is `xfail(strict=True)` labelled
  NOT IMPLEMENTED; against the test-local `ReferenceNoOverwriteGate` (illustration of option 1,
  not product code) each is expected to PASS. A strict XPASS after a real repair means remove the mark.
- `TestUnchangedBehavior`: cap, durability, prewrite failure, ID shape and legacy-key behavior,
  expected PASS for both.
- Expected counts are derived statically from the source in the report, not collected.

## Unresolved semantics

- Cap value, exception type, and whether exhaustion should be a distinct typed error.
- Whether to reserve consumed registry IDs (engine-side check) or leave gate/registry reuse as is.
- Whether retention/archival may delete gate records whose IDs are consumed.
- Auto-approve gates: not changed here.
- Concurrency across processes is covered only by the shared gate lock, the same as the base.
- Does not authenticate anyone; matching IDs or metadata is not authority.
