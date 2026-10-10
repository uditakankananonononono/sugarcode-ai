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

## Status: authored, then RUN after commit 9dcd5470

This section supersedes the original "NOT RUN" text, which stays in
commit 9dcd5470 as history. Commit 9dcd5470 was authored with no test run
(pytest missing). Later, at 00:51:16-18 IST, `python3 -m pip install --user
pytest` succeeded (pytest 9.1.1, pluggy 1.6.0, user site). An earlier
system `pip install pytest` at 00:49:49 failed with a permission error.

Runs at 00:51:26 IST on 9dcd5470 in /tmp/sc (no network):

- New test file: 1 passed.
- New + test_bio_gff.py + test_cli_gff.py: 17 passed.
- tests/self_improve + those same three files: 38 failed, 1819 passed,
  13 xfailed. The 38 failures are unexplained. No cause is claimed and no
  PASS is claimed for this wider selection. They are all under
  tests/self_improve; not investigated.

Mutants at 00:52:02 IST, run in a copy (/tmp/mut), not on the branch.
Original gff.py sha256 `c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`,
restored byte-exact after each (hash verified), restored adjacent
selection 17 passed:

1. Return None instead of the raise: new test failed, DID NOT RAISE.
2. Return text: new test failed, DID NOT RAISE.
3. RuntimeError instead of ValueError: new test failed, RuntimeError escaped.
4. Guard removed (raise replaced by `pass`, guard line kept): new test
   failed, DID NOT RAISE.

Commands (IST): fetches at 00:45:50, 00:47:45, 00:48:07, 00:48:19 against
the public origin; local git, wc, cat, sed, grep, find, py_compile; python3
heredoc text edits to this file; pip commands above; pytest runs above;
cp -r /tmp/sc /tmp/mut and in-copy edits. Full chronology is in the
separately delivered corrected-chronology file. Original "RUN by author"
and mutant-instruction text below the gate is unchanged history.
Separate audit and publication handoff are still required; no push.

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
