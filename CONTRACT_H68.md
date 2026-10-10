# H68 direct frame-three diagnostic

Parent: a4f802f6090e20da4841dc7ddb8d38101974d47c.
Only this contract and one independent test added; no source/old-test edits.
One literal translate('ATG', reading_frame=3) pins exact ValueError type
and 'reading_frame must be 0, 1 or 2'. Direct call only, not explore.
No successful-translation, cleaning, guard-priority, all-frame/type,
genetic-code, consumer/report/model/biology claims.

## Documentary read and overlap gate

2026-10-10 IST: publicca9ec115 verified, full sequence174/bio_utils60 read
22:57:01. Source blob b660260768248d22ee1dfbf4b1cb13e98dd89c89;
direct blob4708c7d6a61495dc35f4a362cee458de4b3a5c56. Fullgene_explorer150
and tests17/spec41 re-read22:57:12, realdata29 read22:57:01.
Direct sequence_iupac12 read22:57:18; codon_input_guards33 read22:57:45.
Tracked diagnostic/frame3 and translate-reference searches found no direct
exact invalid-frame pin. Ordinary/to_stop/IUPAC/codon-clean output tests
partly overlap successful translation, not this rejection.
Existing explore('ATGAAA',reading_frame=3) hits explore's own earlier guard
with different comma text. It does not reach sequence.translate's guard.
Real consumer43 passes reading_frame through after its separate guard.
Scoped static search is not exhaustive dynamic semantic uniqueness.

Parent ratified22:57:36. Publicca9ec115 reverified and sequence72-86 visibly
re-anchored22:57:45 immediately before test authoring. H67 landing interrupt
after initial runs, before mutants/contract/commit; test stayed untouched
and hash-checked during H67 staged==candidate==committed landing. Public
 a4f802f6 reverified and source72-86 re-anchored22:59:30; runs repeated before
mutants/contract. H67 only adds unrelated motif test/contract. Chronology
is documentary self-report, not independent certification.

## Current-source expectation

Valid ATG is cleaned before checking membership of frame3 in(0,1,2).
The literal call raises the specified exact diagnostic. This input does
not distinguish ordering against cleaning failures; no priority claim.
It tests neither successful translation nor other frames/types.

## Actual author receipts; independent audit required

Existing Python3.10.12/pytest9.1.1, no dependency installation.
Pre-H67 new1PASS/.15s; seven-file adjacent43PASS/.82s; same seven plus
self_improve1883PASS/13XFAIL/39.30s. Post-H67 new1PASS/.13s,
adjacent43PASS/.76s,wider1883PASS/13XFAIL/36.16s,no skips.
Seven files: newH68,bio_utils,bio_sequence_iupac,codon_input_guards,
gene_explorer,gene_explorer_realdata,gene_explorer_spec. Wider is not
global suite; thirteen strict-XFAIL canaries are not implemented repairs.

Four independent translate-scoped temporary mutants each1FAIL: remove
guard and allow3 both raise no exception; changed message fails equality;
RuntimeError escapes ValueError context. Named guard-before-clean survivor
1PASS/.19s retained: validATG cannot distinguish guard/cleaning order.
Source byte-exact restored SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.14s; no source mutation committed.

Independent audit and explicit EXECUTE required before publication.

Documentary correction: initial local7a6a772 guessed codon_input_guards34;
actual wc33 caught before final handoff. Contract-only same-parent replacement;
test and all execution receipts unchanged. Original retained, never landed.
