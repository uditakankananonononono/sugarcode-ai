# CFD SpCas9 model provenance

This module implements the Cutting Frequency Determination pairwise off-target
score from Doench JG et al., *Nature Biotechnology* 34, 184-191 (2016), DOI
[10.1038/nbt.3437](https://doi.org/10.1038/nbt.3437).

Both complete machine-readable matrices were vendored from
[`crisprVerse/crisprScore`](https://github.com/crisprVerse/crisprScore), live
verified at commit `cbd6f9f60dc7fb50d14b90485b9561d582caf21e` on 2026-09-21:

- `mismatch_weights.tsv`: 240 substitution/position factors from
  `inst/cfd_cas9/cfd.mm.scores.cas9.txt`; SHA-256
  `636e1d8e65f429db8c578036a673cb4516e896c05f594e3ab134734aab84dafc`
- `pam_weights.tsv`: all 16 dinucleotide PAM factors from
  `inst/cfd_cas9/cfd.pam.scores.cas9.txt`; SHA-256
  `3f83c4f659cda48795312c080f8528984a3ce25f9b2475d79cb80b4835fb3b45`

Parity fixtures come from upstream `tests/testthat/test-offtargets.R`.

## Scope and Missing factors

CFD predicts relative cleavage for 20-nt SpCas9 guide/off-target pairs. It does
not model bulges or indels, chromatin, cell type, genomic copy number, alleles,
or delivery. Those factors are **Missing**. The optional aggregate specificity
is a clearly labeled monotonic summary and not a replacement for the published
pairwise CFD output or a genome-wide search.
