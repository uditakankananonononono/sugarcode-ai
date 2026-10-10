# CFD scoring matrices - provenance

`cfd_mm_scores.json` (240 entries) and `cfd_pam_scores.json` (16 entries) are the
published Cutting Frequency Determination (CFD) off-target penalty matrices from
Doench et al., Nature Biotechnology 34, 184-191 (2016), as distributed with the
CRISPOR source (github.com/maximilianh/crisporWebsite, CFD_Scoring/
mismatch_score.pkl and pam_scores.pkl, fetched 2026-09-21, converted to JSON
verbatim - no recalibration, no refitting).

Mismatch keys: `r<wt_rna_base>:d<complement_of_offtarget_base>,<1-based guide position>`.
Score = product of per-mismatch penalties x PAM penalty (NGG -> GG key = 1.0).

`doench2014_params.json` (70 entries) is the published Rule Set 1 on-target
activity table from Doench et al., Nature Biotechnology 32, 1262-1267 (2014),
as embedded in the CRISPOR efficiency-scoring source (github.com/maximilianh/
crisporWebsite, crisporEffScores.py `doenchParams`, fetched 2026-09-21,
converted to JSON verbatim). Scoring follows the paper's methods: intercept
0.59763615, GC-count terms (gcHigh -0.1665878 / gcLow -0.2026259), position/
dinucleotide weights, logistic transform. Rule Set 1 is the only
on-target table in this file.

Rule Set 2 (Azimuth V3, Fusi & Doench 2016) IS vendored, as a separate file:
`rule_set_2_model.json` holds the full and nopos models (scikit-learn 0.17
GradientBoostingRegressor, 100 depth-3 trees) extracted from Microsoft's
Azimuth saved-model pickles (source: https://github.com/MicrosoftResearch/Azimuth,
BSD-3-Clause; license text in LICENSES/AZIMUTH-BSD-3-CLAUSE.txt) and evaluated
by `rule_set_2.py`. The 947-guide fixture figure (max abs error 5.1e-10) is a
historical value stored in that JSON's own conversion note; it was not
re-measured for this note. The upstream commit and the exact pickle bytes are
not pinned in this repository. See the section "crispr_opt Rule Set 2 model
data" in the root PROVENANCE.md.
