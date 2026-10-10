# H110: literal two-field BED record rejection (authored; pytest NOT RUN)

## Scope
Two additions only: `tests/test_h110_bed_two_fields_characterization.py` and this contract. Product source and existing tests unchanged. One literal `parse_bed("chr1\t0")` call pins exact exception type `ValueError` (`type(...) is ValueError`) and exact text `line 1: BED record has 2 fields, need >= 3`. Source finding only (bed.py 23-25: split on tab gives 2 fields, `len(f) < 3` raises before any coordinate indexing at line 29). No all-short-widths, tab-semantics, successful-parse, BED-standard, consumer, model or biology claim. Authority: peer scope for H110 relayed by Main (12:45:37 AM IST, attached scope file) and Main's pytest-missing decision (12:46:52 AM IST); not independently authenticated by me.

## Overlap disclosure
H82 (tests/test_h82_bed_short_record_characterization.py, CONTRACT_H82.md) pins the one-field `parse_bed("chr1")` -> "BED record has 1 fields, need >= 3" through the same guard; this is the two-field literal through the same branch with a different count in the text. Direct malformed-input regexes in test_bio_bed.py (block validation, invalid interval, score) hit other branches. No existing test or contract mentions "2 fields" (grep over tests and CONTRACT_*.md, 12:47:13, empty).

## Read gate and chronology (2026-10-11 IST, visible)
Base: `git clone` of the public repo 00:45:44-45 (tip c39c761c); `git fetch origin` 00:46:59 found b870d171 (H108, adds only CONTRACT_H108.md and its test); fast-forwarded. Re-fetch 00:47:26 immediately before authoring: origin/main = HEAD = b870d171d71d3c974638d84d1ffccd432d195e5c (tree 0a60c069ab61ffa6a9207747d6162d9e74efe957, parent c39c761c0334654a34804adc7d60b4f51b2fec74).
Full reads at that tip, 00:47:07-13: src/sugarcode/bio/bed.py 1-180 (180 lines, blob cdaf35e536e26de74b34b8312a8cff7ab23d57e8); tests/test_bio_bed.py 1-95 (blob 533b14adff0f59a38e2030409ec5e432d5d911a2); tests/test_cli_bed.py 1-44 (blob ccc9822ba156fdaf567704b9e2fd23d0fcdaf7f0); tests/test_h82_bed_short_record_characterization.py 1-12 (blob 408c7f473f4e7827c8763cfffacc91e847463a06); CONTRACT_H82.md 1-53 (blob 88519bce139865d8d8c3969c58fb8e844d5d82c3). NOT read: other CLI regions, bed_prefix_schema.py. Test written 00:47:27 (quoted heredoc cat, no scripted edit), contract afterward.

## Expected literal (source-derived)
"chr1\t0": not blank, no track/browser/# prefix, `split("\t")` -> ["chr1","0"], len 2 < 3 -> ValueError(f"line 1: BED record has 2 fields, need >= 3").

## What was RUN and NOT RUN
pytest is not installed in this workspace (no install permitted). NOT RUN: pytest on the new test, adjacent selections (test_bio_bed, test_cli_bed), wider tests/self_improve selection, and every mutation rerun. RUN (non-pytest only): git clone/fetch/rev-parse/diff, sed/cat/grep reads, python3 --version, a non-writing syntax compile of the new test file (`python3 -B -c "compile(...)"`, output compile-ok), and one direct `PYTHONPATH=src python3 -B -c` call of parse_bed("chr1\t0") printing `True 'line 1: BED record has 2 fields, need >= 3'`. That direct call is not a pytest result and no PASS is claimed.

## Mutants for the peer to run (NOT RUN by me; each from original source, one at a time, restore byte-exact and verify SHA256, rerun adjacent)
1. Return None instead of raising at bed.py 25 (replace `raise ValueError(...)` with `return None`): expected DID NOT RAISE ValueError, exit 1.
2. Return the diagnostic text instead of raising (`return f"line {ln}: ..."`): expected DID NOT RAISE, exit 1.
3. Raise RuntimeError with the same text at line 25: RuntimeError escapes, exit 1.
4. Remove the field-count guard (delete lines 24-25): `f[2]` at line 29 raises IndexError (list index out of range), which escapes instead of an accepted record; exit 1.
Expected exits are source-derived predictions, not observed.

## Suggested peer commands (not run by me)
`PYTHONPATH=src python -B -m pytest -q tests/test_h110_bed_two_fields_characterization.py`; then that file + tests/test_bio_bed.py + tests/test_cli_bed.py; then the same selection + tests/self_improve (record counts and strict XFAIL separately; never the global suite).
