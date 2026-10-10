# H75 sequence-module empty molecular-weight equality

Parent: 216bc1cc70e8451dc5ed77f2465fe0befcbbd4df.
Two additions only: this contract and one independent test. No source or
old-test edits. One literal sugarcode.bio.sequence.molecular_weight('')
==0.0 equality only. No output-type validation, mass-table values,
water/bond correction, valid/invalid residues, chemical accuracy,
consumer correctness, model or biology claims.

## Documentary read gate and distinction

2026-10-10 IST: fullsequence174/bio_utils60/proteinprops-test107 and
protein_painter_realdata46 read23:16:11. Initial proposal guessed106 for
proteinprops-test; actual wc107 corrected23:16:28 before authoring.
Source blob b660260768248d22ee1dfbf4b1cb13e98dd89c89;
bio_utils blob4708c7d6a61495dc35f4a362cee458de4b3a5c56.
Consumer protein_painter1-110 read including import4 and call102.
Tracked molecular_weight references show empty rejection in
sugarcode.bio.proteinprops, a DIFFERENT module, not this sequence API.
Painter's imported sequence-function tests use nonemptyGGG/A and overlap
nonempty arithmetic only. No direct sequence-module empty pin found.
Scoped static search is not exhaustive dynamic semantic uniqueness.
Read-only explicit sequence-module probe returned repr0.0 at23:16:11.

Parent ratified author-only execution23:16:39, explicitly no push.
Public216bc1cc reverified23:16:46, source166-167 visibly re-anchored before
writing test. Empty iterator sum0 minus18.02*max(0,-1) predicts0.0.
This source explanation is not a water/bond or mass-table validation claim.
Read chronology is documentary self-report, not independent certification.

## Actual runtime receipts; independent audit required

Existing Python3.10.12/pytest9.1.1, no dependency installation.
New1PASS/.12s; four-file adjacent17PASS/1moduleSKIP/.49s;
same four plus self_improve1857PASS/1moduleSKIP/13XFAIL/41.44s.
Four files: newH75,bio_utils,bio_proteinprops,protein_painter_realdata.
Module-level importorskip Bio at proteinprops-test90 skips the ENTIRE file,
including pre-oracle empty-rejection assertions. Direct newH75 executes;
no claim that different-module rejection tests executed in this env.
Skip-only reason check1SKIP/.19s exited5 (no tests collected); set-e stopped
that batch before mutants. Next batch performed mutants, not a rerun of
missing work claimed done. Wider is not global suite; thirteen strict-XFAIL
canaries are not implemented repairs.

Four independent temporary mutants each1FAIL: unclamped len-1 correction
returns18.02; added offset returns1.0; returnNone fails equality; empty1/0
raisesZeroDivisionError. Named omit-water survivor1PASS/.12s,
changed-A-mass survivor1PASS/.17s and integer-zero survivor1PASS/.17s
retained. Empty iterator never looks up mass values; omitted correction
also equals zero; equality cannot distinguish int0 from float0.0.
No mass, water/bond or output-type claim inferred from these receipts.
Source byte-exact restored SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.14s; no source mutation committed.

Independent audit and explicit publication EXECUTE required; not pushed.
