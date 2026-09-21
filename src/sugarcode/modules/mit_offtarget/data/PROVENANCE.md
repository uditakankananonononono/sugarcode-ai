# MIT/Hsu off-target model provenance

This module implements the MIT pairwise off-target score described by Hsu et
al., *Nature Biotechnology* 31, 827-832 (2013), DOI
[10.1038/nbt.2647](https://doi.org/10.1038/nbt.2647), and its standard aggregate
guide-specificity formula.

Machine-readable artifacts were vendored from
[`crisprVerse/crisprScore`](https://github.com/crisprVerse/crisprScore), live
verified at commit `cbd6f9f60dc7fb50d14b90485b9561d582caf21e` on 2026-09-21:

- `position_weights.tsv`, upstream `inst/mit/mit.weights.txt`, SHA-256
  `467d6e821a03b2b2b6caa97bc913b2c35302640e37ec93c85375b3a2ebf80dcb`
- `pam_weights.tsv`, upstream `inst/cfd_cas9/cfd.pam.scores.cas9.txt`, SHA-256
  `3f83c4f659cda48795312c080f8528984a3ce25f9b2475d79cb80b4835fb3b45`

The PAM table is the published SpCas9 PAM activity table used by the upstream
MIT implementation. Pairwise parity fixtures are copied from upstream
`tests/testthat/test-offtargets.R`.

## Limits

The score applies to 20 nt SpCas9 guides. It is a heuristic cleavage-risk
model, not a measured probability. Aggregate specificity is only as complete
as the genomic candidate sites supplied by the caller. Bulges, indels,
chromatin state, cell type, alleles, and genomic copy number are **Missing**.
