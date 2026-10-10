# H118: literal numeric phase-three GFF pin

## Scope and overlap

Exactly two additions: this contract and
`tests/test_h118_gff_phase_three_characterization.py`.
Source and existing tests unchanged.

One `parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t3\tID=g')` call
pins exact ValueError type and `line 1: invalid phase '3'` text.
Literal phase3 is numeric but not in the current guard set.
H91 phase-x pins same guard with different literal. Removing guard here
accepts record with int phase3; H91 instead reaches raw int ValueError.
H118 is numeric-three literal only, no generic diagnostic novelty or
phase-policy claim. Source-derived diagnostic, not external format oracle.
No other inputs, successful-parse pin, format/conformance, coordinate,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base `ce6d644e42fe596a0f760074579f3b8f35375594`.
2026-10-11 IST: parent assignment received at 00:52:45; public HTTPS fetch
at 00:52:48 re-anchored onto fresh actual tip ce6d644e. Full gff.py,
direct/CLI tests and H91 contract visibly read before authoring. Shared
H91 guard disclosed above. Contract claims do not authenticate permission;
this private candidate follows the received parent assignment only.
No exhaustive collision-search claim. Chronology is author self-report,
not independent certification.

## Actual receipts

Python 3.10.12, pytest 9.1.1, existing private environment.

- New: 1 passed, new.xml.
- New + bio_gff + cli_gff: 17 passed, adjacent.xml.
- tests/self_improve + same three files: 1857 passed, 13 xfailed,
  wider.xml. Selected suite, not global suite.
- Restored-source adjacent: 17 passed, restored.xml.

Four independent temporary mutants fail new-only with exit 1:

1. Return None: DID NOT RAISE ValueError.
2. Return full text: DID NOT RAISE ValueError.
3. RuntimeError class: escapes.
4. Remove phase guard: accepts record with phase3,
   DID NOT RAISE ValueError.

Each mutant starts from original bytes. Finally-block source restoration,
source cache removal and byte-exact comparison performed.
Restored gff.py SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Archive includes XML/log/reproducer; manifest supplies candidate, tree,
parent and committed addition blobs. No mutations committed. Separate
audit/publication handoff required; no push by this author.
