# H70 literal no-valid-base diagnostic

Parent: 4a1bfbc4e963662fc073561eb3c2398ba891d152.
Two additions only: this contract and one independent test. No source or
old-test changes. One literal clean_dna('123-') pins exact ValueError type
and 'sequence contains no valid DNA bases'. Direct call only.
No general cleaning, all-invalid-input, successful-cleaning, ambiguity,
coordinate, consumer-output/report/model/biology claims.

## Documentary read gate and overlap

2026-10-10 IST: full sequence174 and direct sequence_iupac12 read23:04:37;
full bio_utils60 and consumer gene_explorer150 read23:04:49. Their relevant
existing consumer tests17/realdata29/spec41 were fully read during H68
22:57:01-12, before this proposal; reused for
adjacent context. Source blob b660260768248d22ee1dfbf4b1cb13e98dd89c89;
bio_utils blob4708c7d6a61495dc35f4a362cee458de4b3a5c56.
Tracked clean_dna and exact-diagnostic searches found only direct
ambiguity-success coverage, no no-valid-base exact rejection pin. Real
consumer explore30 calls clean_dna. This is not a no-caller claim or a
consumer-output assertion. Scoped static search is not exhaustive dynamic
semantic uniqueness. Read chronology is documentary self-report, not
independent certification.

Parent ratified author-only execution23:05:05, explicitly no push.
Public4a1bfbc4 reverified by ls-remote23:05:14; relevant source54-62 visibly
re-anchored immediately before authoring. Source filters literal digits
and hyphen, leaving empty s; empty-result guard gives the asserted text.
This input tests neither normalization nor ambiguity or valid-base output.

## Author runtime receipts; independent audit required

Existing Python3.10.12/pytest9.1.1, no dependency installation.
New1PASS/.12s; six-file adjacent33PASS/.66s; same six plus
self_improve1873PASS/13XFAIL/35.20s, no skips. Six files: newH70,
bio_utils,bio_sequence_iupac,gene_explorer,gene_explorer_realdata,
gene_explorer_spec. Wider is not global suite; thirteen strict-XFAIL
canaries are not implemented repairs.

Four independent clean_dna-scoped temporary mutants each1FAIL: remove
empty guard and retain unfiltered input each raise no exception; changed
classRuntimeError escapes context; changed diagnostic fails equality.
Named omit-upper survivor1PASS/.12s retained: digit/hyphen literal cannot
distinguish uppercase normalization, so no normalization claim.
Source byte-exact restored SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.11s; no source mutation committed.

Independent audit and explicit publication EXECUTE required; not pushed.
