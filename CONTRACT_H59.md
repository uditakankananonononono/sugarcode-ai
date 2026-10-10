# H59 thirteen-adenine short-branch arithmetic

Parent: 8360ec272b7b95e812d33bf55591b806dbfb450f.
Only this contract and one independent test added. No source or old-test
changes. One literal tm_wallace('AAAAAAAAAAAAA') == 26.0 pin only.
No PBS design/report, physical melting accuracy, model or biology claims.

## Documentary scope and read gate

Original H59 Newick root5/A-missing/B2 proposal was dropped before authoring
as a near-duplicate of P09, at parent acceptance22:30:15 on2026-10-10 IST.
Neither defined-root fixture discriminates including root in missing count.
Replacement ratified22:30:58: exactly13 adenines and direct equality26.0.

Initial replacement proposal guessed185 source lines and no production
caller. Corrected before authoring22:30:32: sequence.py174 lines, source
blob b660260768248d22ee1dfbf4b1cb13e98dd89c89; bio_utils60 lines,
blob4708c7d6a61495dc35f4a362cee458de4b3a5c56. Prime_design/core calls
at42 and68 are real consumers. Those corrections remain in this record.

Full sequence174/bio_utils60 re-read22:34:02 on public251f4634. Full
prime_design/core518 and tests prime_design17/spec73 re-read22:34:08;
published42 read22:31:05. Source PBS_RANGE10-16; old tests accept through17.
This observation creates no H59 design/report assertion. Complete tracked
Wallace reference search22:34:08 found only source, prime_design import/
calls and existing ATGC short arithmetic test. Boundary collision search
found no direct13-A/26 pin; primer homopolymer tests use tm_nn, distinct API.
Search is static and scoped, not exhaustive dynamic semantic uniqueness.

P09 then H60 landing priority completed before authoring. Current public
8360ec272b7b95e812d33bf55591b806dbfb450f verified by ls-remote22:35:33;
sequence107-114 visibly re-anchored immediately before writing the test.
Reads/chronology are documentary self-report, not independent proof.

## Source-derived expectation and overlap

Current source cleans the sequence, uses long formula only if len(s)>13,
and otherwise returns2*(A+T)+4*(G+C). For this literal13-A input the short
expression yields26.0. Existing ATGC test partly overlaps short arithmetic
but does not pin the13 boundary. This test does not establish14 behavior,
all boundary transitions, cleaning, T/G/C contributions or general accuracy.

## Author execution receipts, independent audit required

Existing Python3.10.12/pytest9.1.1. No new dependency installation.
New1PASS/.12s; new+bio_utils+prime_design+prime_design_spec+
prime_design_published38PASS/.87s; samefive+tests/self_improve1878PASS/
13XFAIL/38.80s, no skips. Selected wider run is not global suite; thirteen
strict-XFAIL canaries are not implemented repairs.

Four independent temporary mutants each1FAIL: len(s)>=13, short A/T
coefficient3, omit A from short count, short return0. Named survivor
len(s)>14 gives1PASS/.14s: this literal13 input cannot distinguish moving
the transition later. This limitation is retained, not coverage of14.
Source restored byte-exact SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.11s; no source mutation committed.

Independent audit and explicit EXECUTE required before publication.
