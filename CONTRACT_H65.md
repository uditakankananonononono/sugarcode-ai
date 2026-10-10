# H65 literal empty hydrophobicity profile

Parent: 5976b7ae6da57c89115b75a590f611acc3c937fd.
Only this contract and one independent test added. No source or old-test
changes. One direct literal hydrophobicity_profile('') == [] pin only.
No consumer outputs, scale accuracy, other-window/residue, protein/design/
report/model/biology claim.

## Documentary read and overlap gates

2026-10-10 IST: full sequence174 read22:50:24, source blob
b660260768248d22ee1dfbf4b1cb13e98dd89c89. Full gene_explorer150 and
protein_painter169 read22:51:30, blobs respectively
 e4152909a6f2c9f16d840d9d1dcbbf592e060723 and
 7d74826651a8b16978fd6c506261a7fff7006bef.
Bio_utils60 and consumer tests gene_explorer17/realdata29,
protein_painter_spec22 read22:51:30; gene_explorer_spec41 and
protein_painter_realdata46 read22:51:37. A guessed nonexistent
 test_protein_painter.py read failed; actual listed files read instead.
No phantom-file coverage claimed. Real consumers gene_explorer63 and
protein_painter59 call this API; no no-caller claim.

Tracked symbol and hydrophobicity/empty searches found no direct empty
profile pin. Alpha_fold_ui test hydrophobicity term belongs to a different
API; consumer tests partly overlap downstream use but not this literal
empty-input call. Scoped static search is not exhaustive dynamic proof.
Parent ratified22:51:42. Public5976b7ae reverified by ls-remote22:51:49;
source170-174 visibly re-anchored immediately before writing the test.
Read chronology is documentary self-report, not independent certification.

## Current-source expectation

Empty input produces empty vals. Default window9 makes len(vals)<window
true. The vals-false branch returns[] without evaluating sum(vals)/len(vals).
This characterizes this literal returned list only; it does not establish
nonempty behavior, scale values, other windows or arbitrary-input safety.

## Actual author receipts; independent audit required

Existing Python3.10.12/pytest9.1.1, no dependency installation.
New1PASS/.19s; seven-file adjacent46PASS/.92s; same seven plus
 tests/self_improve1886PASS/13XFAIL/35.13s, no skips. Seven files: newH65,
bio_utils, gene_explorer, gene_explorer_realdata, gene_explorer_spec,
protein_painter_realdata, protein_painter_spec. Wider is not global suite;
thirteen strict-XFAIL canaries are not implemented repairs.

Four independent temporary mutants each1FAIL: remove vals guard causes
ZeroDivisionError; return[0.0], returnNone each fail equality; force empty
branch1/0 causes ZeroDivisionError. Named scale-zero survivor1PASS/.11s:
empty input cannot test scale lookup values, no scale claim inferred.
Source byte-exact restored SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.13s; no source mutation committed.

Independent audit and explicit EXECUTE required before publication.
