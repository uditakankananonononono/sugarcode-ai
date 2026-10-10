# H96: exact second GTF item missing-value diagnostic

## Scope

Exactly two additions: this contract and
`tests/test_h96_gtf_missing_value_characterization.py`. No product source or
existing test changes.

One literal call:
`parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tgene_id "g"; bad')`.
Pin exact exception identity `ValueError` and exact text
`line 1: malformed GTF attribute 'bad'`. First quoted gene_id selects the
current GTF branch; second literal item bad lacks a value. Diagnostic is
source-derived. No other malformed inputs, general format/conformance,
consumer, model, accuracy or biology claims.

## Documentary read gate

Base: `0a00272fb958696ff4c59f3fadc565789d0c67a2`.
2026-10-11 IST: parent ratified at 00:11:21. Fresh public HTTPS fetch at
00:11:25 re-anchored onto 0a00272f. Full gff.py, test_bio_gff.py and
test_cli_gff.py were visibly read before authoring. Those direct tests do
not pin this literal branch. No exhaustive collision-search claim.
Chronology is author self-report, not independent certification.

## Actual receipts

Python 3.10.12 and pytest 9.1.1 in the existing private environment.

- New: 1 passed, new.xml.
- New + bio_gff + cli_gff: 17 passed, adjacent.xml.
- tests/self_improve + same three files: 1857 passed, 13 xfailed,
  wider.xml. This selection is not the global suite.
- Restored-source adjacent: 17 passed, restored.xml.

Four independent temporary mutants all fail the new test with exit 1:

1. Return None at malformed-item guard: caller raises unpacking TypeError.
2. Changed diagnostic to bad GTF attribute: exact text fails.
3. Changed exception class to RuntimeError: exception escapes.
4. Removed guard and raise: parts[1] access raises IndexError.

Each mutant starts from original bytes. Finally-block restoration, source
cache removal and byte-exact comparison performed. Restored gff.py SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Archive includes XML, mutant log and reproducer. Manifest supplies candidate,
parent, tree and committed new-file blobs. No mutations committed. Separate
audit and publication handoff remain required; no push by this author.
