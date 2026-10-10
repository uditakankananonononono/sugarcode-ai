# Prospective proposal commit admission

Base84eed10. Real registry.save_proposal now validates and encodes the complete
prospective registry BEFORE candidates mkdir or candidate/test file writes.
Same J02 schema and F02 16MiB cap, no new limits. _encode_state shared with _save
prevents admission policy drift; _save validates again before atomic commit.
Corrupt registry from R01 preflight now raises RegistryError with original
RegistryValidationError cause, consistent with registry._load. Low-level pure
preflight helper exception remains unchanged. Filesystem/path/byte exceptions
not broadly normalized. This is a deliberate public boundary exception change,
callers catching old RegistryValidationError must catch RegistryError instead.

Discovered defect repaired: exactly-full valid registry could leave an EMPTY
candidates directory when prospective bytes exceeded cap. Now schema/size refusal
precedes even mkdir; tests cover actual16MiB and smaller probe plus bytes/no-dir.
Existing valid Unicode identifiers, generic kinds and unknown finite extension
fields remain supported. No overwrites or identical retries. Existing postreplace
AtomicDurabilityError retains referenced candidate files, verified unchanged.

NOT cross-file atomicity or race containment. In-process registry lock only,
external writer/ancestor swap races, hard-crash orphan files, later IO failure
empty dirs and cleanup failure still possible. Preflight successful encoding
costs memory and is repeated at commit; not RSS/CPU budget. No signature or grant.
Source code/test admission remains the separate source wiring unit, not here.

7new tests run, including2parameterized capacity cases and3corruption cases;
30focused tests cover new cases + existing10R01 and13atomic wiring cases.
Broad selected count in bundle; separate independent verdict required before
landing. No paid service, model/biology or parked PRIDICT work.
