# H64: blank-only read_jaspar rejection

## Scope

Two additions only: `tests/test_h64_jaspar_blank_only_characterization.py`
and this contract. Product source and existing tests are unchanged.

One literal call, `read_jaspar("\n \t\n")`, pins exact exception type
`ValueError` and exact text `no JASPAR matrices found`. The current loop
skips both blank lines, leaves the header unset and motifs empty, and
reaches the final no-matrices guard. This is current-code characterization,
not a successful-parse, format-standard, PWM, accuracy, or biological claim.

## Read and re-anchor record

Base: `1624a6d68c499ee0f8aed5ce94ce2844b5bf2787`.
The read-only proposal followed full reads of `src/sugarcode/bio/motif.py`,
`tests/test_bio_motif.py`, `tests/test_cli_motif.py`, the CLI motif loader
and handlers, and repository coverage searches. Existing tests pin
before-header, missing-row, unequal-length, nonnumeric-token, and invalid
prefix cases, but no pre-existing blank-only/no-matrices literal pin was
found. Parent ratified this two-file scope.

Immediately before authoring, public main was fetched over HTTPS and
verified at the base above; source and both direct test files were visibly
read in full. The CLI consumer and coverage search were read again after
authoring. This chronology is an author self-report, not independent audit.

## Actual receipts

Python 3.10.12 and pytest 9.1.1. Selections:

- New test: 1 passed (`new.xml`).
- Adjacent: new test plus `test_bio_motif.py`, `test_cli_motif.py`,
  `test_h52_jaspar_nonnumeric_characterization.py`, and
  `test_h60_jaspar_row_prefix_characterization.py`: 11 passed (`adjacent.xml`).
- Wider: `tests/self_improve` plus that same adjacent selection:
  1851 passed, 13 xfailed (`wider.xml`). This is not the global suite.
- Restored-source adjacent selection: 11 passed (`restored.xml`).

Four independent temporary mutants each failed the new test with exit 1:

1. Remove the final no-matrices guard: no exception raised.
2. Replace its diagnostic with `no matrices`: exact text assertion fails.
3. Replace its exception class with RuntimeError: exception escapes.
4. Remove the blank-line skip: exact text assertion fails with
   `line 1: matrix row before any header`. The proposal's anticipated
   IndexError was incorrect; this receipt records the actual failure.

Mutants were each applied to original source, with source restored in a
finally block and caches removed. Byte-exact restoration was checked.
Restored motif source SHA256:
`74252072c1cd38b37e4fb1b1b4d9b10de9d6e872722bce0359b1d98da57a6902`.
The private receipt archive contains XMLs, mutant log and reproducer.
Candidate/tree/parent and committed new-file blobs are in the manifest.
