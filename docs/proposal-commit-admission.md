# Prospective proposal commit admission

Base 84eed10. Real registry.save_proposal now validates and encodes the complete
prospective registry BEFORE candidates mkdir or candidate/test file writes.
Same J02 schema and F02 16 MiB cap, no new limits. _encode_state shared with _save
prevents admission policy drift; _save validates again before atomic commit.
Corrupt registry from R01 preflight now raises RegistryError with original
RegistryValidationError cause, consistent with registry._load. Low-level pure
preflight helper exception remains unchanged. Filesystem/path/byte exceptions
not broadly normalized. This is a deliberate public boundary exception change,
callers catching old RegistryValidationError must catch RegistryError instead.

Discovered defect repaired: exactly-full valid registry could leave an EMPTY
candidates directory when prospective bytes exceeded cap. Now schema/size refusal
precedes even mkdir; tests cover actual 16 MiB and smaller probe plus bytes/no-dir.
Existing valid Unicode identifiers, generic kinds and unknown finite extension
fields remain supported. No overwrites or identical retries. Existing postreplace
AtomicDurabilityError retains referenced candidate files, verified unchanged.

NOT cross-file atomicity or race containment. In-process registry lock only,
external writer/ancestor swap races, hard-crash orphan files, later IO failure
empty dirs and cleanup failure still possible. Preflight successful encoding
costs memory and is repeated at commit; not RSS/CPU budget. No signature or grant.
Source code/test admission remains the separate source wiring unit, not here.

7 new tests run, including 2 parameterized capacity cases and 3 corruption cases;
30 focused tests cover new cases + existing 10 R01 and 13 atomic wiring cases.
Broad selected count in bundle; separate independent verdict required before
landing. No paid service, model/biology or parked PRIDICT work.

Counts above are parameterized test cases, not function definitions. Builder
environment selected 1,065 passed (1,058 base + 7 new), no skips. Independent
auditor reproduced delta +7 with zero new failures: 985 candidate / 978 base
passed, with the same 23 environment-dependent failures on both. These absolute
counts are environment-specific; builder did not reproduce those 23 failures.
The independent auditor also verified all 7 new cases fail against the base.
The local candidate hash was not public during review; review used matching
patch/tree bytes, not a published commit.
