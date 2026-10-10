# H111: literal ten-field GFF record rejection

## Scope

Two additions only: `tests/test_h111_gff_ten_fields_characterization.py`
and this contract. Product source and existing tests remain unchanged.

One literal `parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tID=g\textra')` call
(ten tab-separated fields) pins exact exception identity `ValueError` and
exact text `line 1: GFF record has 10 fields, need 9`. Expected text is
derived from reading current source: the guard `len(f) != 9` raises with
`len(f)` and the line number. It is not a parser oracle. No all-widths,
standards, line-numbering, attribute, successful-parse, consumer, model,
or biology claim.

H90 overlap: H90 pins one field (`parse_gff("chr1")`, "has 1 fields").
This test pins a different width on the over-wide side of the same guard
and the same exception type. Existing `test_malformed_inputs_raise` uses
three fields and substring `need 9`.

## Status: authored NOT RUN

No test was executed. pytest is not installed in the author environment
and no install was permitted. Every test result is NOT RUN. No pass is
claimed. The peer audits and runs it.

RUN by author (read-only, no pytest): `git fetch origin`, `git checkout`,
`git rev-parse`, `wc -l`, `cat -n`, `sed`, `grep`, `python3 --version`
(3.10.12), `python3 -m py_compile` on the new test (syntax only).

## Documentary read gate

Base: `05fc2a6040ad8a49b13077a613d1e468592ec8f9` (H109, fetched 00:48:07 IST). Reads
were done at c39c761 (fetch 00:45:50 IST); fetch at 00:47:45
moved origin/main to b870d17 (H108), fetch at 00:48:07 to 05fc2a6 (H109).
Target delta c39c761..05fc2a6 is additions only (see diff names in report); gff.py, test_bio_gff.py, test_cli_gff.py and CONTRACT_H90.md are
byte-identical between c39c761 and b870d17, and unchanged b870d17..05fc2a6 (git diff --quiet).

Read: `src/sugarcode/bio/gff.py` 1-130 (blob 42babd53...),
`tests/test_bio_gff.py` full 119 lines (cb320d9f...),
`tests/test_cli_gff.py` full 40 lines (35bcd826...),
`CONTRACT_H90.md` and its test, `tests/test_h107_*`. NOT read: gff.py
131-237, other contracts. Grep of tests/ and CONTRACT_*.md for
`need 9`, `GFF record has`, `10 fields` found only H90 and
`test_bio_gff.py` (greps run at c39c761; H108/H109 files not read or grepped). No exhaustive collision-search claim. Chronology is
author self-report.

## Mutants for the peer to run (NOT RUN by author)

Each starts from original `parse_gff` in gff.py; restore after each.
Expected: new test fails (derived from source reading, not observed).

1. Return None: replace the `raise ValueError(...)` in the field-count
   guard with `return None`. Expect DID NOT RAISE.
2. Return text: replace it with `return text`. Expect DID NOT RAISE.
3. RuntimeError: change `ValueError` to `RuntimeError` in that raise.
   Expect RuntimeError escapes `pytest.raises(ValueError)`.
4. Remove field-count guard: delete the two lines
   `if len(f) != 9:` / `raise ValueError(...)`. The ten-field line then
   returns a record (f[9] unused), so expect DID NOT RAISE.

No mutation is committed. Separate audit and publication handoff are
required; no push by this author.
