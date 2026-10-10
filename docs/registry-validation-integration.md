# Registry strict JSON/schema read and pre-serialization validation

Base2aefa5a. Peer J02 PREP helper/tests/fixtures retained and actually run locally.
Parent policy2026-10-10: preserve Unicode alphanumeric plus '-'/'_' IDs and generic
nonempty kind strings; unknown finite JSON extension fields preserved. Contiguous
ordered versions1..N, valid active reference, nonnegative timestamps, paired
rollback time/approval, known proposed/activated proposal status enforced. Empty
gap string allowed, proposal approval_id nullable even after direct activation.
No arbitrary ASCII/128/six-kind restriction. Existing caller/lifecycle tests pass.

_load now strict-decodes raw UTF8 bytes and validates schema/module before returns;
RegistryValidationError becomes RegistryError with cause. _save validates entire
JSON tree/schema and strict encodes allow_nan=False before atomic helper. Invalid
history unchanged and whole-read refused, no migration/skip. Invalid prospective
save unchanged. Schema is source-derived policy, not independently measured
historical-corpus compatibility. Unknown extension fields must be valid exact JSON
builtins, finite floats; cycles/custom subclasses/keys refuse. No byte/depth/value
caps, hostile alias expansion or universal parser memory/CPU guarantee.

This is NOT proposal-write preflight: save_proposal still writes code/test files
BEFORE _load; corrupt registry can leave orphan/overwritten candidates. That
SC-R01 repair remains separate and queued. Other operations may mutate files
before save fails; no multi-file transaction/effects rollback guarantee. Low-level
activate accepts caller approval_id without authenticating human intent; metadata
shape/digest not authority. Paths strings schema only; containment/race rules
remain existing behavior. Unknown future schema/status incompatible files need
manual review; no automatic conversion. IO/MemoryError/OverflowError outside
RegistryError normalization. Atomic durability uncertainty remains F01 contract.

Peer98 authored cases PASS,8 new actual-wiring cases PASS; selected416 PASS/no
skips (main310+98+8). F01 failure tests changed only invalid registry save fixture
{'new':1} to VALID registry object+new field, so injected IO is still exercised
rather than prematurely blocked by new schema. Initial3 failures recorded, then
fixed fixture. Base wiring comparison reported separately; no helper-existence
completion/clinical/model/science claim. Independent verdict required.

Independent VERIFIED schema verdict,416PASS reproduced. Known boundary: stored
version/code/test paths only nonempty strings; existing containment at activation,
no end-to-end traversal proof. Whole-state bad row refuses. IO/MemoryError/
OverflowError outside typed RegistryError. J02 alone prevalidation orphan gap is
closed only by R01 stack, therefore landed together. F02 byte caps separate unit.
