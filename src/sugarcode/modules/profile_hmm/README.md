# Profile HMM

Profile hidden Markov models built from a multiple alignment, following
Durbin, Eddy, Krogh & Mitchison, *Biological Sequence Analysis* (Cambridge
University Press 1998, ISBN 978-0-521-62971-3), Chapter 5, and Krogh et al.
1994 (J Mol Biol 235:1501). Pure algorithm, numpy only.

```python
from sugarcode.modules.profile_hmm import build_profile_hmm, viterbi, forward

m = build_profile_hmm(["HEAGAWGHEE", "HEAGAW-HEE", "HDAGAWGHEE", "HEAG-WGHEE"])
m.consensus()                        # 'HEAGAWGHEE'
v = viterbi(m, "HEAGAWHEE")
v["state_path"]  # ['M1','M2','M3','M4','M5','M6','D7','M8','M9','M10']
v["log_prob"], v["bits"], v["log_odds"]
forward(m, "HEAGAWHEE")["log_prob"]  # sum over all paths
```

- States: Begin, M1..ML, I0..IL, D1..DL, End. All nine transition types of
  Durbin Fig. 5.2 (including D->I and I->D). The last position goes only to End or I_L.
- Match columns: gap fraction <= `gap_threshold` (default 0.5; columns that are
  more than half gaps become insert columns), or pass `match_columns` explicitly.
- Pseudocounts: `pseudocount` on emissions (Laplace 1 by default),
  `transition_pseudocount` on every existing transition (defaults to the same).
- Insert emissions: counted (default) or `"background"`. Background for log-odds
  is `"uniform"`, `"alignment"` frequencies, or a mapping you pass in.
- Alphabet: DNA, RNA or protein, inferred or given. T/U are swapped to match the model.
- Scores are natural-log probabilities, plus bits and log-odds against an
  i.i.d. background.
- No local/glocal (HMMER Plan7-style) mode, no Dirichlet mixture priors, no
  sequence weighting, no Baum-Welch training. This is the Durbin Chapter 5
  global model built from an alignment.

Verification: tiny-model fixtures computed by hand as exact fractions
(construction, Viterbi 64/735, a 5-path Forward sum, insert and delete paths).
`brute_force()` enumerates every Begin->End state path without DP, and it
matches Viterbi (max) and Forward (sum) to 1e-9 relative on 100+ random small
alignments and sequences.
