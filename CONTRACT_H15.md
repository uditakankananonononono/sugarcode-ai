# CONTRACT_H15: microbiome_exp analyze_16s richness counts positive-support taxa (AUTHORED, NOT RUN)
Base 4d5292004feff70fc896be1bae774158e95eb215 (microbiome_exp/core.py blob 915ff52cefe6c9804c6f39834a99c738fac53150). Authority: peer rulings relayed by Main, not independently authenticated by me.
Second replacement (supersedes cc09a8f7, which replaced 88f1ae7f): source and test byte-identical to it, contract sentence pair (a)/(b) added. Chronology of the original (IST, 10 Oct 2026): test written 16:15:03-16:15:08; source edited 16:15:08-16:15:09; this contract after. Tests before source (self-reported).
## Change
- analyze_16s: richness = sum(1 for c in counts.values() if c > 0), was len(counts). One line. A taxon present with a zero count no longer counts. Shannon, simpson, relative abundance, dominant genera, functions, flags and the return shape are untouched.
- Valid inputs only. NOT changed: the empty-table guard (`if not counts or sum(counts.values()) <= 0: raise ValueError("empty count table")`), so {} and all-zero tables still raise ValueError; tests/test_microbiome_phage.py test_16s_rejects_empty is unaffected. No validation widening, no abundance-diversity change.
- (a) Taxa with non-positive counts are excluded from richness. Mixed input with a positive total is accepted, and its non-positive taxa are excluded from richness (this includes a negative count alongside positive counts; analyze_16s still does not validate negatives).
- (b) Input with total <= 0, all-zero input, or all-negative input still raises the preserved ValueError("empty count table"); the guard is unchanged.
- Negative and mixed-negative inputs are described only as preserved behavior (analyze_16s did not validate negatives before and does not after) and remain OUTSIDE the ruled valid domain; no validation is added or widened for them.
- cohort_analysis already computes richness as int(np.sum(p>0)) and is not edited.
## Tests (tests/test_h15_richness_positive_support.py)
- Frozen hand-computed cases: {'A':10,'B':0} -> 1; {'A':5,'B':3} -> 2. A zero-count taxon changes none of shannon/simpson/richness.
- {} and {'A':0,'B':0} raise ValueError matching "empty count table".
- Cross-check against cohort_analysis on mixed positive valid samples {s1:{A:10,B:0}, s2:{A:5,B:3}}: cohort richness per sample equals analyze_16s richness (1 and 2). Cohort's actual validation boundary (reported, not broadened): at least two samples, each a non-empty dict of integers >= 0 with a positive total; the tests pin that an all-zero sample and a single-sample table raise ValueError.
- Existing tests that read richness: test_microbiome_exp_spec (richness == 3 for a three-taxon positive sample) and test_microbiome_phage (richness == 6 for six positive taxa): unchanged by reading, not run.
## RUN vs NOT RUN
NOT RUN: all tests, imports. RUN: git, sha256sum, text edits only.
