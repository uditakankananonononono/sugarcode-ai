# CRISPRscan model provenance

`coefficients.csv` contains the 91 position-specific mono/di-nucleotide
coefficients and intercept for the CRISPRscan / Moreno-Mateos score.

- Primary paper: Moreno-Mateos MA et al., *Nature Methods* 12, 982-988 (2015),
  DOI: [10.1038/nmeth.3543](https://doi.org/10.1038/nmeth.3543)
- Machine-readable distribution: `crisprVerse/crisprScore`, file
  `inst/crisprscan/crisprscan_coefficients.csv`
- Repository: <https://github.com/crisprVerse/crisprScore>
- Source commit live-verified 2026-09-21:
  `cbd6f9f60dc7fb50d14b90485b9561d582caf21e`
- Raw URL: <https://raw.githubusercontent.com/crisprVerse/crisprScore/cbd6f9f60dc7fb50d14b90485b9561d582caf21e/inst/crisprscan/crisprscan_coefficients.csv>
- Vendored artifact SHA-256:
  `6e3f1bbfd58e5426651a15cfd0db6ac2094e0a93158dc51639b5929fc9ced5a4`

The implementation follows the reference implementation's one-based feature
positions and additive linear score. The five locked parity fixtures in the
tests are copied from that repository's `tests/testthat/test-crisprscan.R`.

## Applicability limits

The model requires exactly 35 nt: 6 upstream bases, the 20 nt spacer, canonical
NGG PAM, and 6 downstream bases. It was trained on T7-transcribed SpCas9 guides
in zebrafish. A score is **Missing** when the full context is unavailable or
ambiguous. No claim of calibration for U6 expression, non-SpCas9 nucleases,
non-NGG PAMs, or other experimental systems is made.
