# H112: literal missing GTF opening quote

PREP-NORUN: test file authored, NOT RUN under pytest (pytest absent, no
install permitted). Every test and mutant result below is NOT RUN.

Exactly two additions: this contract and
tests/test_h112_gtf_missing_opening_quote_characterization.py.
One parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tgene_id "g"; gene_name g"')
call pins exact ValueError type and exact text:
line 1: malformed GTF attribute 'gene_name g"'
First item gene_id "g" is valid and quoted, so GTF is selected. Second item:
len(parts)=2 and endswith quote true; ONLY the startswith quote check fails
(gff.py line 53, raise line 54).
Overlap: H96 and H107 cover the same branch with a different condition and
diagnostic ('bad' and 'gene_id "g'). This pins the missing-opening-quote
literal only. Source-derived repr diagnostic, not an external GTF oracle.
No other input, quoting, conformance, success-path, biology or accuracy claim.
No source or existing-test edits. Instructions reached me via the parent
relay of the peer scope; the scope file itself grants nothing.

## Read gate

Live tip b870d171d71d3c974638d84d1ffccd432d195e5c (H108), fetched and
verified 2026-10-11 00:47:33 IST immediately before authoring. gff.py blob
42babd534fb5f86fa916b162c17d52e34feb4bd3 (237 lines; 1-110 read in full,
111-237 not read). H107 test and contract, H96 test, tests/test_bio_gff.py
malformed section and tests/test_cli_gff.py head read. Scoped
"malformed GTF attribute" collision grep NOT run beyond those files.

## RUN vs NOT RUN

NOT RUN: the new test under pytest; all mutants; any suite.
RUN (no pytest): one direct python3 probe of the literal on the live source
(00:47:42 IST) printed type is ValueError True, text equal True. One
py_compile of the new test, exit 0. Probe is a read-only check, not the test.

## Mutants for the peer to run (NOT RUN, each from original bytes)

1. Return None in the branch: caller unpacking raises TypeError, test fails.
2. Return ('gtf', {}): record accepted, no raise, test fails.
3. Raise RuntimeError instead of ValueError: type check fails.
4. Remove ONLY the startswith clause at line 53: record accepted, no raise,
   test fails.
Restore source and compare bytes after each.
