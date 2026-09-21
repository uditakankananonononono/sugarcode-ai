# CFD scoring matrices - provenance

`cfd_mm_scores.json` (240 entries) and `cfd_pam_scores.json` (16 entries) are the
published Cutting Frequency Determination (CFD) off-target penalty matrices from
Doench et al., Nature Biotechnology 34, 184-191 (2016), as distributed with the
CRISPOR source (github.com/maximilianh/crisporWebsite, CFD_Scoring/
mismatch_score.pkl and pam_scores.pkl, fetched 2026-09-21, converted to JSON
verbatim - no recalibration, no refitting).

Mismatch keys: `r<wt_rna_base>:d<complement_of_offtarget_base>,<1-based guide position>`.
Score = product of per-mismatch penalties x PAM penalty (NGG -> GG key = 1.0).
