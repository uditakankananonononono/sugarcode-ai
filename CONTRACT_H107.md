# H107: literal missing GTF closing quote

Exactly two additions: this contract and
 tests/test_h107_gtf_missing_closing_quote_characterization.py.
One parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tgene_id "g') call pins
exact ValueError identity and exact text:
line 1: malformed GTF attribute 'gene_id "g'
Embedded opening double quote preserved in literal expected diagnostic.
len(parts)=2, startswith quote true; only endswith quote fails at53/raise54.
H96 same branch, different len(parts) condition and diagnostic ('bad').
Distinct missing-closing-quote literal/condition only. Source-derived
repr diagnostic, not external GTF oracle. No other input, broad quoting,
conformance, successful parse, consumer, model, accuracy or biology claim.
No source/existing-test edits; comments not validated.

## Read gate

Base/live public re-anchor341097f4401eb09d58e4d5d570d24894a3a4c05b
verified2026-10-11 00:39:06 IST before authoring. Fresh full gff.py,
direct/CLI tests and H96 test/contract visibly read. Scoped H-test/contract
search found H96 branch overlap but no same missing closing quote pin;
not exhaustive absence. Source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Literal probe confirmed identity/text. Parent ratified00:39:00.
Chronology is author self-report, not independent certification.

## Actual runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
Final literal-only expected text: new1P/.13s, new+direct+CLI17P/.71s,
same+tests/self_improve1857P/13X/37.87s. Selected, not global suite;
XFAILs not implemented repairs. Restored new1P/.11s.
Initial equivalent text used trailing-space rstrip; replaced with pure literal
before committing, reran all receipts/mutants. Earlier passes were1/17/1857+13X,
not additional coverage; final receipts describe committed test.
Four independent new-only mutants, all1FAIL/exit1:
- ReturnNone/.13s: caller unpacking TypeError, not accepted record.
- Return tuple('gtf',{})/.12s: accepted record, did not raise.
- RuntimeError/.13s: escapes.
- Remove only endswith clause/.12s: accepted record, did not raise.
Each starts from original bytes; finally restoration/cache removal and
byte-equality check, final source SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full log/reproducer supplied with per-receipt manifest hashes.
No exhaustive mutant adequacy claim. No push; separate audit/publication required.
