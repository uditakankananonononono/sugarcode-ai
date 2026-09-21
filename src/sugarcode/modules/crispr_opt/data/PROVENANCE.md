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
dinucleotide weights, logistic transform. Rule Set 2 (Fusi/Azimuth 2016) is
NOT vendored: its gradient-boosted sklearn model files are not portably
loadable on modern numpy/sklearn - status: Missing, labeled wherever relevant.
