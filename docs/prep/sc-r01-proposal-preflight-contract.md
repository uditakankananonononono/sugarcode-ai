# SC-R01 preparation contract

Base: ba0eb275f182e77a4f24530b668e3e17f2528df5.
Status: PREP ONLY. Tests authored, not run. No existing paths or wiring changed.
The original save_proposal still writes candidate files before loading registry.
This helper is not a completed repair or evidence that the method is safe.

## Explicit dependency seam

The injected validator now matches the supplied SC-J02 PREP decoder interface:

    decode_registry_json(raw: str | bytes, *, expected_module: str) -> dict[str, Any]

SC-J02 owns strict JSON decoding and full registry validation, including duplicate
keys, finite numbers, exact built-in shapes, module binding, proposal/feature
schema and version invariants. Invalid input raises and never returns a partial
state. The returned object is an exact built-in dict with an exact built-in
proposals dict. The callback must not mutate files. No J02 import, implementation or
permissive fallback is invented here. Pass SC-J02's decode_registry_json directly
as validate_registry; R01 calls it with bytes and keyword-only expected_module.
It returns an exact dict; RegistryValidationError (ValueError subclass) and its
cause propagate unchanged. validate_registry_state alone is not sufficient: it
does not decode bytes. No J02 code is copied or applied on this branch. The actual
combined call has not been run. Both PREP contracts still need peer acceptance.
Test validators are keyword-only fixtures, not J02 implementations.

No dependency on J04 is introduced. No approval encoding, reading or J04 duplicate
is included. F01 could provide registry persistence after preflight, but this
helper neither serializes registry state nor calls F01.

## Proposed overwrite and identity policy (pending acceptance)

Every previously registered key is refused, even identical retries and records
with either proposed or activated status (the current J02 PREP enum). A new key
also refuses either preexisting target,
including orphan files, directories, regular/broken symlinks. No bytes are
replaced and no existing record is refreshed. Retry callers must query the
existing record explicitly or select a fresh key after reviewing the conflict.
This is deliberate refusal-only idempotency, not successful no-op replay.

Keys/module slugs: 1-128 ASCII letters/digits/hyphens/underscores, first character
alphanumeric. Feature names: 1-128 lowercase ASCII letters/digits/underscores,
first character a letter. The six kinds match CAPABILITY_KINDS at the pinned base.
These limits are a proposed filesystem identity policy, not an existing schema
fact. SC-J02 permits Unicode alphanumeric plus hyphen/underscore IDs without this
length rule, arbitrary nonempty kind strings, and broader proposal names. R01 is
intentionally stricter for new candidates only; J02 still validates existing rows.
Peer must decide the shared identity policy before integrating. Existing
FeaturePlan/Candidate callers need compatibility review. Legacy
records are validated by J02; the new-name rule is not applied to unrelated rows.
Input fields are exact strings. Code/test source must encode strictly as UTF-8;
no execution, AST quality check or generated-test safety claim is made. Gap
signature may be empty, matching both the pinned save_proposal and SC-J02 PREP.
No hash-derived key binding is required: the pinned base
has both digest-prefix keys and tests with k-prefixed keys.

The module_dir must already exist and be caller-selected for module_slug. Every
ancestor must be a plain directory, registry.json a plain regular file, and an
existing candidates entry a plain directory. Symlinks are refused, not resolved
into trusted paths. Missing registry refuses. Missing candidates is permitted but
not created. Absolute paths are lexical normalization of the trusted argument;
the helper cannot establish which module directory the owner authorized.

## Integration owner requirements, not implemented here

1. Hold the registry's coordination lock before reading registry or inspecting
   candidates, through the eventual registry save. The existing threading lock
   is process-local; shared writers need separate coordination or explicit refusal.
2. Call this helper before mkdir or any candidate write. Adapt its errors without
   losing the SC-J02 cause. Do not use _load's bare json.loads as the validator.
3. Recheck registry snapshot using registry_sha256 before commit if the lock cannot
   exclude external writers. A digest is a change detector, not authentication.
4. Use exclusive create/no-follow for candidate files, and directory-handle-based
   path containment or equivalent trusted-directory protection. lstat/read_bytes
   here has TOCTOU windows; read-only preflight is not a race-proof reservation.
5. Prepare the record from the returned bytes/digests/paths and reviewed time,
   status and approval contracts. Use strict pre-serialization and reviewed
   single-file persistence. On failures before registry save, remove only new
   files this attempt created, never someone else's destination.
6. Obtain real integrated canaries: corrupt/ambiguous registry and unsafe identity
   refuse before candidate mkdir/write; conflicts preserve all bytes; normal
   proposal/activation still work; injected failures preserve snapshots as scoped.
   Peer owns existing-method edits, test execution and independent verdict.

Single-file atomic replacement does not make registry plus two candidate files
crash-atomic. No cross-file transaction, exactly-once, human authentication,
resource isolation, or protection against hostile concurrent filesystem changes
is claimed. No cap reader/F02 functionality is duplicated.

## Authored test scope

The new test file exercises the standalone preflight helper only and contains
byte-snapshot fixtures for refusals. It neither invokes the vulnerable existing
method nor proves it repaired. The integration tests above remain outstanding.
No tests, pytest, migrations, services or PostgreSQL were run in preparation.
