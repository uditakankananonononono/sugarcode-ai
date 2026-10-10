# Telemetry JSON ambiguity and serialization error repair

Candidate based on main 8a4fd410bfa2f9d5ccc3b8955fcaf9040d072b9e.
Scope: GapEventStore only, not every JSON reader in SugarCode.

Historical object decoding rejects duplicate decoded keys at every object depth.
Identical duplicate values are also refused. Unicode-escaped keys are compared
AFTER JSON decoding, so "a" and "\u0061" conflict. Equal keys in different objects
do not conflict. A rejected row raises indexed InvalidTelemetryValue and leaves
the original bytes unchanged; no migration, filtering or recovery guess.

Fresh appends snapshot exact builtins first, then serialize before opening the
append file. JSON encoder ValueError, TypeError and RecursionError are translated
to InvalidTelemetryValue with the original cause. This includes an integer beyond
the active interpreter decimal-string limit. No portable numeric-size cap is
added; interpreters with different or disabled limits can behave differently.
IO failures, MemoryError and other runtime errors are not normalized. No claim
of transactional append, cross-process locking or total typed-error coverage.

The original reviewed doc's statements "duplicate keys are not rejected" and
"fail closed with plain ValueError, not the typed InvalidTelemetryValue" remain
historical statements about candidate 554a9bf. This new candidate changes those
two behaviors within GapEventStore only; it does not rewrite audit history.

Builder tests: 14 new parameterized test cases. On original main with those tests
copied in: 13 failed, 1 passed, confirming regression canaries detect the missing
behavior. On candidate: 14 passed; complete self_improve directory 129 passed
(115 existing plus 14 new). These counts are not independent gate verdicts,
full configured-suite coverage, CI matrix acceptance or scientific evaluation.

Unchanged limits: decoding has no byte/line/resource cap, post-decode traversal
bounds only, no authenticity/permission/model-quality boundary. Old activation,
other JSON readers, signature custody and production containment remain separate.

## Independent verdict and archive-only limitations

Independent verdict, relayed 2026-10-10: VERIFIED for the stated scope
(GapEventStore duplicate-key refusal and pre-append serialization typing), with
SCOPED residue. Verifier reproduced 14 candidate canaries and 13 failures/1 pass
on the reconstructed base, plus extra decoding and no-created-file probes.

It did not rerun the broader 129/146 selections: archive omitted the modules
needed for those imports; raw/JUnit receipts were internally consistent only.
It could not verify candidate commit identity or remote main from the archive.
Builder verifies those separately before/after landing; not a reviewer claim.

engine.py:71, gate.py:43, registry.py:37 and isolated_dispatch.py:48 still use
plain json.loads; no repository-wide duplicate-key claim. OSError, MemoryError
and OverflowError are not normalized. One rejected historical row blocks the
whole store read by design; no partial-good-row return or history migration.
